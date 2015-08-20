# -*- coding: utf-8 -*-

import json
from time import sleep
from pagador import servicos


TEMPO_MAXIMO_ESPERA_NOTIFICACAO = 30


class Ambiente(object):
    test = 'T'
    live = 'L'


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.query_string
        self.chave_api = str(getattr(self.configuracao, 'token', ''))
        self.chave = 'api_key'

    def obter_credenciais(self):
        return self.chave_api


MENSAGEM_DADOS_INVALIDOS = {
    'customer[phone][ddd]': u'O DDD do seu número de telefone está faltando ou é inválido.',
    'customer[phone][number]': u'O seu número de telefone está faltando ou é inválido.',
    'customer[address][zipcode]': u'O seu CEP está faltando ou é inválido.',
}


MENSAGENS_RETORNO = {
    'processing': 'Pagamento sendo processado',
    'authorized': 'Pagamento autorizado',
    'paid': 'Pagamento aprovado',
    'refused': 'Pagamento recusado',
    'waiting_payment': 'Aguardando pagamento',
    'pending_refund': 'Pagamento em disputa',
    'refunded': 'Pagamento retornado'
}


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao()
        self.conexao.tenta_outra_vez = False
        self.url = 'https://api.pagar.me/1/transactions'
        self.dados_pagamento = {}

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def envia_pagamento(self, tentativa=1):
        if self.pedido.situacao_id and self.pedido.situacao_id != servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO:
            self.resultado = {
                'sucesso': self.pedido.situacao_id == servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
                'situacao_pedido': self.situacao_pedido,
                'alterado_por_notificacao': False
            }
            next_url = self.dados.get('next_url', None)
            if next_url:
                self.resultado['next_url'] = next_url
            raise self.PedidoJaRealizado(
                u'Já foi realizado um pedido com o número {} e ele está como {}.\n{}'.format(
                    self.pedido.numero,
                    servicos.SituacaoPedido.NOMES_SITUACAO[self.pedido.situacao_id],
                    servicos.SituacaoPedido.mensagens_complementares(self.pedido.situacao_id)
                )
            )
        self.dados_enviados = self.malote.to_dict()
        self.resposta = self.conexao.post(self.url, self.dados_enviados)

    def _verifica_erro_em_conteudo(self, titulo):
        mensagens = []
        titulo_substituto = []
        invalid_parameter = False
        if 'conteudo_json' not in self.dados_pagamento:
            self.dados_pagamento['conteudo_json'] = {'mensagem_retorno': ''}
        if self.resposta.conteudo:
            erros = self.resposta.conteudo.get('errors', None)
            if erros:
                for erro in erros:
                    if erro['type'] == 'invalid_parameter':
                        invalid_parameter = erro['parameter_name'] != 'card_hash'
                        mensagens.append(u'{}: {}'.format(erro['parameter_name'], erro['message']))
                        titulo_substituto.append(MENSAGEM_DADOS_INVALIDOS.get(erro['parameter_name'], erro['message']))
                    elif erro['type'] == 'action_forbidden' and 'refused' in erro['message']:
                        return False
                    elif erro['type'] == 'action_forbidden' and 'processing' in erro['message']:
                        return True
                    else:
                        mensagens.append(erro['message'])
            else:
                mensagens.append(json.dumps(self.resposta.conteudo))
        if invalid_parameter:
            titulo = u'\nDados inválidos:\n{}'.format('\n'.join(titulo_substituto))
        mensagens.append(u'HTTP STATUS CODE: {}'.format(self.resposta.status_code))
        self.dados_pagamento['conteudo_json']['mensagem_retorno'] = titulo
        raise self.EnvioNaoRealizado(
            titulo,
            self.loja_id,
            self.pedido.numero,
            dados_envio=self.dados_enviados,
            erros=mensagens,
            status=(400 if invalid_parameter else 500)
        )

    def processa_dados_pagamento(self):
        if self.pedido.conteudo_json['pagarme'].get('metodo', '') == 'boleto':
            processado = self.processa_dados_pagamento_boleto()
        else:
            processado = self.processa_dados_pagamento_cartao()
        if processado:
            return
        if self.resposta.requisicao_invalida or self.resposta.nao_autorizado:
            self.situacao_pedido = SituacoesDePagamento.do_tipo('refused')
            titulo = u'A autenticação da loja com o PAGAR.ME falhou. Por favor, entre em contato com nosso SAC.' if self.resposta.nao_autorizado else u'Ocorreu um erro nos dados enviados ao PAGAR.ME. Por favor, entre em contato com nosso SAC.'
            if not self._verifica_erro_em_conteudo(titulo):
                self.resultado = {'sucesso': False, 'mensagem': u'nao_aprovado', 'situacao_pedido': self.situacao_pedido, 'fatal': True}
        else:
            self.situacao_pedido = SituacoesDePagamento.do_tipo('refused')
            self._verifica_erro_em_conteudo(u'Não foi obtida uma resposta válida do PAGAR.ME. Nosso equipe técnica está avaliando o problema.')

    def processa_dados_pagamento_boleto(self):
        if self.resposta.sucesso:
            sucesso = self.resposta.conteudo['status'] == 'waiting_payment'
            if sucesso:
                self.dados_pagamento = {
                    'transacao_id': self.resposta.conteudo['id'],
                    'valor_pago': self.formatador.formata_decimal(self.pedido.valor_total),
                    'conteudo_json': {
                        'metodo': 'boleto',
                        'aplicacao': self.configuracao.aplicacao,
                        'boleto_url': self.resposta.conteudo['boleto_url'],
                        'codigo_barras': self.resposta.conteudo['boleto_barcode'],
                        'vencimento': self.resposta.conteudo['boleto_expiration_date'],
                    }
                }
                self.identificacao_pagamento = self.resposta.conteudo['id']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(self.resposta.conteudo['status'])
            self.resultado = {'sucesso': sucesso, 'situacao_pedido': self.situacao_pedido, 'alterado_por_notificacao': False}
            return True
        return False

    def processa_dados_pagamento_cartao(self):
        tempo_espera = TEMPO_MAXIMO_ESPERA_NOTIFICACAO
        while tempo_espera:
            pedido = self.cria_entidade_pagador('Pedido', numero=self.pedido.numero, loja_id=self.configuracao.loja_id)
            if pedido.situacao_id not in [servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO, servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE]:
                self.situacao_pedido = None
                self.resultado = {'sucesso': True, 'situacao_pedido': pedido.situacao_id, 'alterado_por_notificacao': True}
                return True
            sleep(1)
            tempo_espera -= 1
        if self.resposta.sucesso:
            self.dados_pagamento = {
                'transacao_id': self.resposta.conteudo['id'],
                'valor_pago': self.formatador.formata_decimal(self.pedido.valor_total),
                'conteudo_json': {
                    'metodo': 'cartao',
                    'bandeira': self.resposta.conteudo['card_brand'],
                    'aplicacao': self.configuracao.aplicacao,
                    'mensagem_retorno': MENSAGENS_RETORNO.get(self.resposta.conteudo['status'], u'O pagamento pelo cartão informado não foi processado. Por favor, tente outra forma de pagamento.'),
                    'numero_parcelas': int(self.dados_cartao.get('parcelas', 1)),
                    'valor_parcela': float(self.dados_cartao.get('valor_parcela', '0.0')),
                }
            }
            self.identificacao_pagamento = self.resposta.conteudo['id']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(self.resposta.conteudo['status'])
            self.resultado = {'sucesso': self.resposta.conteudo['status'] == 'processing', 'situacao_pedido': self.situacao_pedido, 'alterado_por_notificacao': False}
            return True
        return False

    @property
    def dados_cartao(self):
        return self.pedido.conteudo_json.get('pagarme', {})

    @property
    def tem_parcelas(self):
        parcelas = self.dados_cartao.get('parcelas', 1)
        return int(parcelas) > 1


class SituacoesDePagamento(servicos.SituacoesDePagamento):
    DE_PARA = {
        'processing': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'authorized': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'paid': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        'refused': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
        'waiting_payment': servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO,
        'pending_refund': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA,
        'refunded': servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO
    }

DE_PARA_SITUACOES = {
    servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE: 'Pagamento sendo processado',
    servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO: 'Pagamento aprovado',
    servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO: 'Pagamento recusado',
    servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO: 'Aguardando pagamento',
    servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA: 'Pagamento em disputa',
    servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO: 'Pagamento retornado'
}


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)
        self.faz_http = True
        self.conexao = self.obter_conexao()
        self.url = 'https://api.pagar.me/1/transactions/{}'
        self.dados_pagamento = {}

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def obtem_informacoes_pagamento(self):
        if 'id' in self.dados:
            self.url = self.url.format(self.dados['id'])
            self.resposta = self.conexao.get(self.url)

    @property
    def transacao_id(self):
        return self.dados.get('id', None)

    @property
    def pedido_id(self):
        return self.dados.get('referencia', None)

    @property
    def status(self):
        return self.dados.get('current_status', None)

    def parcela(self, numero, valor_pago):
        self.configuracao.adiciona_parcelas_disponiveis(valor_pago)
        for parcela in self.configuracao.parcelas_disponiveis:
            if int(parcela['numero']) == int(numero):
                return parcela
        return {'valor_parcelado': 0.0}

    def monta_dados_pagamento(self):
        self.pedido_numero = self.pedido_id
        self.situacao_pedido = SituacoesDePagamento.do_tipo(self.status)
        if self.resposta and self.resposta.sucesso:
            valor_pago = self.formatador.formata_decimal(float(self.resposta.conteudo['amount']) / 100)
            if self.resposta.conteudo['payment_method'] == 'credit_card':
                numero_parcela = int(self.resposta.conteudo.get('installments', 1))
                self.dados_pagamento = {
                    'transacao_id': self.dados['id'],
                    'valor_pago': valor_pago,
                    'conteudo_json': {
                        'metodo': 'cartao',
                        'bandeira': self.resposta.conteudo['card_brand'],
                        'aplicacao': self.configuracao.aplicacao,
                        'mensagem_retorno': MENSAGENS_RETORNO.get(self.resposta.conteudo['status'], u'O pagamento pelo cartão informado não foi processado. Por favor, tente outra forma de pagamento.'),
                        'numero_parcelas': numero_parcela,
                        'valor_parcela': self.parcela(numero_parcela, valor_pago)['valor_parcelado'],
                    }
                }
            else:
                self.dados_pagamento = {
                    'transacao_id': self.dados['id'],
                    'valor_pago': valor_pago,
                    'conteudo_json': {
                        'metodo': 'boleto',
                        'aplicacao': self.configuracao.aplicacao,
                        'boleto_url': self.resposta.conteudo['boleto_url'],
                        'codigo_barras': self.resposta.conteudo['boleto_barcode'],
                        'vencimento': self.resposta.conteudo['boleto_expiration_date'],
                    }
                }
            self.resultado = {'resultado': 'OK'}
        else:
            self.resultado = {'resultado': 'FALHA', 'status_code': 500}

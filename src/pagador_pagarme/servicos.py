# -*- coding: utf-8 -*-

import json
from pagador import servicos


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


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        if dados['passo'] == PassosDeEnvio.pre:
            self.servico = PreEnvio(loja_id, plano_indice, dados=dados)
        if dados['passo'] == PassosDeEnvio.captura:
            self.servico = CompletaPagamento(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.servico.conexao = self.obter_conexao()
        self.url = 'https://api.pagar.me/1/transactions'
        self.servico.url = self.url
        self.servico.entrega = self

    def define_credenciais(self):
        self.servico.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def define_pedido_e_configuracao(self, pedido_numero):
        super(EntregaPagamento, self).define_pedido_e_configuracao(pedido_numero)
        self.servico.configuracao = self.configuracao
        self.servico.pedido = self.pedido

    def montar_malote(self):
        self.servico.extensao = self.extensao
        self.servico.montar_malote()

    def envia_pagamento(self, tentativa=1):
        self.servico.envia_pagamento(tentativa)

    def _verifica_erro_em_conteudo(self, titulo):
        mensagens = []
        if self.resposta.conteudo:
            erros = self.resposta.conteudo.get('errors', None)
            if erros:
                for erro in erros:
                    if erro['type'] == 'invalid_parameter':
                        mensagens.append(u'{}: {}'.format(erro['parameter_name'], erro['message']))
                    else:
                        mensagens.append(erro['message'])
            else:
                mensagens.append(json.dumps(self.resposta.conteudo))
        mensagens.append(u'HTTP STATUS CODE: {}'.format(self.resposta.status_code))
        raise self.EnvioNaoRealizado(
            titulo,
            self.loja_id,
            self.pedido.numero,
            dados_envio=self.dados_enviados,
            erros=mensagens
        )

    def processa_dados_pagamento(self):
        if self.resposta.sucesso:
            self.dados_pagamento = {
                'transacao_id': self.resposta.conteudo['id'],
                'valor_pago': self.pedido.valor_total
            }
            self.identificacao_pagamento = self.resposta.conteudo['id']
            self.servico.processa_dados_pagamento()
        elif self.resposta.requisicao_invalida or self.resposta.nao_autorizado:
            titulo = u'A autenticação da loja com o PAGAR.ME falhou. Por favor, entre em contato com nosso SAC.' if self.resposta.nao_autorizado else u'Ocorreu um erro nos dados enviados ao PAGAR.ME. Por favor, entre em contato com nosso SAC.'
            self._verifica_erro_em_conteudo(titulo)
        else:
            self._verifica_erro_em_conteudo(u'Não foi obtida uma resposta válida do PAGAR.ME. Nosso equipe técnica está avaliando o problema.')


class PreEnvio(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(PreEnvio, self).__init__(loja_id, plano_indice, dados=dados)
        self.conexao = None
        self.url = None
        self.entrega = None

    def envia_pagamento(self, tentativa=1):
        self.entrega.dados_enviados = self.malote.to_dict()
        self.entrega.resposta = self.conexao.post(self.url, self.entrega.dados_enviados)

    def processa_dados_pagamento(self):
        self.entrega.dados_pagamento = {
            'conteudo_json': {
                'bandeira': self.entrega.resposta.conteudo['card_brand'],
                'aplicacao': self.configuracao.aplicacao
            }
        }
        if self.tem_parcelas:
            self.entrega.dados_pagamento['conteudo_json'].update({
                'numero_parcelas': int(self.dados['cartao_parcelas']),
                'valor_parcela': float(self.dados['cartao_valor_parcela']),
                'sem_juros': self.dados['cartao_parcelas_sem_juros'] == 'true'
            })
        self.entrega.resultado = {'sucesso': self.entrega.resposta.conteudo['status'] == 'processing'}

    @property
    def tem_parcelas(self):
        parcelas = self.dados.get('cartao_parcelas', 1)
        return int(parcelas) > 1

    def montar_malote(self):
        super(PreEnvio, self).montar_malote()


class CompletaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(CompletaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.conexao = None
        self.url = None
        self.entrega = None

    def envia_pagamento(self, tentativa=1):
        pedido_pagamento = self.cria_entidade_pagador('PedidoPagamento', loja_id=self.configuracao.loja_id, pedido_numero=self.pedido.numero, codigo_pagamento=self.configuracao.meio_pagamento.codigo)
        pedido_pagamento.preencher_do_banco()
        self.entrega.resposta = self.conexao.post('{}/{}/capture'.format(self.url, pedido_pagamento.identificador_id))

    def processa_dados_pagamento(self):
        self.entrega.situacao_pedido = SituacoesDePagamento.do_tipo(self.entrega.resposta.conteudo['status'])
        self.entrega.resultado = {'sucesso': self.entrega.situacao_pedido == SituacoesDePagamento.DE_PARA['processing']}

    def montar_malote(self):
        pass


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


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)

    @property
    def transacao_id(self):
        return self.dados.get('id', None)

    @property
    def pedido_id(self):
        return self.dados.get('referencia', None)

    @property
    def status(self):
        return self.dados.get('current_status', None)

    def monta_dados_pagamento(self):
        self.pedido_numero = self.pedido_id
        self.situacao_pedido = SituacoesDePagamento.do_tipo(self.status)
        self.resultado = {'resultado': 'OK'}

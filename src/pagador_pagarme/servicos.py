# -*- coding: utf-8 -*-

from li_common.comunicacao import requisicao

from pagador import settings, servicos


class Ambiente(object):
    test = 'T'
    live = 'L'


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.form_urlencode
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
        self.servico.conexao = self.obter_conexao(formato_envio=requisicao.Formato.form_urlencode)
        self.servico.url = 'https://api.pagar.me/1/transactions'
        self.servico.entrega = self

    def define_credenciais(self):
        self.servico.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def define_pedido_e_configuracao(self, pedido_numero):
        super(EntregaPagamento, self).define_pedido_e_configuracao(pedido_numero)
        self.servico.configuracao = self.configuracao
        self.servico.pedido = self.pedido

    def montar_malote(self):
        super(EntregaPagamento, self).montar_malote()
        self.servico.malote = self.malote

    def envia_pagamento(self, tentativa=1):
        self.servico.envia_pagamento(tentativa)

    def processa_dados_pagamento(self):
        if self.resposta.sucesso:
            self.dados_pagamento = {
                'transacao_id': self.resposta.conteudo['tid'],
                'valor_pago': self.pedido.valor_total,
                'conteudo_json': {
                    'bandeira': self.resposta.conteudo['card_brand'],
                    'aplicacao': self.configuracao.aplicacao
                }
            }
            self.identificacao_pagamento = self.resposta.conteudo['id']
            self.servico.processa_dados_pagamento()
        if self.resposta.requisicao_invalida:
            erros = self.resposta.conteudo.get('errors', None)
            if erros:
                mensagens = []
                for erro in erros:
                    if erro['type'] == 'invalid_parameter':
                        mensagens.append(u'{}: {}'.format(erro['parameter_name'], erro['message']))
                    else:
                        mensagens.append(erro['message'])
                raise self.EnvioNaoRealizado(
                    u'Dados inválidos enviados ao PAGAR.ME',
                    self.loja_id,
                    self.pedido.numero,
                    dados_envio=self.malote.to_dict(),
                    erros=mensagens
                )


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
        if self.tem_parcelas:
            self.entrega.dados_pagamento['conteudo_json'].update({
                'numero_parcelas': int(self.dados['cartao_parcelas']),
                'valor_parcela': float(self.dados['cartao_valor_parcela']),
                'sem_juros': self.dados['cartao_parcelas_sem_juros'] == 'true'
            })
        self.entrega.resultado = {'sucesso': self.entrega.resposta.conteudo['status'] == 'authorized'}

    @property
    def tem_parcelas(self):
        parcelas = self.dados.get('cartao_parcelas', 1)
        return int(parcelas) > 1


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
        self.entrega.resultado = {'sucesso': self.entrega.situacao_pedido == SituacoesDePagamento.DE_PARA['paid']}


class SituacoesDePagamento(servicos.SituacoesDePagamento):
    DE_PARA = {
        'paid': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        'refused': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO
    }

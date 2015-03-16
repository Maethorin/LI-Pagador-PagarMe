# -*- coding: utf-8 -*-
from li_common.comunicacao import requisicao

from pagador import settings, servicos


MENSAGENS_REJEICAO = {
    '-1': None,
    '00': None,
    '51': u'Produto ou serviço não habilitado para o estabelecimento. Entre em contato com a Rede.',
    '53': u'Transação não permitida para o emissor. Entre em contato com a Rede.',
    '56': u'Erro nos dados informados. Tente novamente. Ao receber este erro na transação de confirmação da pré (fulfill), importante reenviar a transação diariamente durante 3 dias e caso persista o erro entrar em contato com nosso suporte técnico.',
    '57': u'Estabelecimento inválido.',
    '58': u'Transação não autorizada. Contate o emissor.',
    '65': u'Senha inválida. Tente novamente.',
    '69': u'Transação não permitida para este produto ou serviço.',
    '72': u'Contate o emissor.',
    '74': u'Falha na comunicação. Tente novamente.',
    '79': u'Cartão expirado. Transação não pode ser resubmetida. Contate o emissor.',
    '80': u'Transação não autorizada. Contate o emissor. (Saldo Insuficiente).',
    '81': u'Produto ou serviço não habilitado para o emissor (AVS).',
    '82': u'Transação não autorizada para cartão de débito.',
    '83': u'Transação não autorizada. Problemas com cartão. Contate o emissor.',
    '84': u'Transação não autorizada. Transação não pode ser resubmetida. Contate o emissor.',
}


class StatusDeRetorno(object):
    sem_resposta = '-1'
    sucesso = '1'
    comunicacao_interrompida = '2'
    timeout = '3'
    erro_nos_dados = '5'
    erro_na_comunicacao = '6'
    nao_autorizado = '7'
    fulfill_nao_executado = '19'
    tipo_cartao_invalido = '21'
    referencia_invalida = '22'
    data_expiracao_invalida = '23'
    cartao_expirado = '24'
    numero_cartao_invalido = '25'
    numero_cartao_incompleto = '26'
    cartao_ainda_invalido = '29'
    valor_invalido = '34'
    referencia_em_uso = '51'
    cartao_usado_recentemente = '56'
    xml_invalido = '60'
    erro_configuracao = '61'
    cv2_incompleto = '132'
    estabelecimento_invalido_1 = '480'
    estabelecimento_invalido_2 = '482'
    tempo_limite_para_autorizacao = '1104'
    revisao = '1127'
    rejeitada = '1126'
    rsg_invalido = '1130'


MENSAGENS_RETORNO = {
    StatusDeRetorno.sucesso: u'Seu pagamento foi aprovado com sucesso.',
    StatusDeRetorno.sem_resposta: u'A Rede não está disponível no momento. Por favor, tente mais tarde. Se o erro persistir, contacte o SAC da loja.',
    StatusDeRetorno.comunicacao_interrompida: u'Ocorreu um erro de comunicação com a Rede. Por favor, tente de novo.',
    StatusDeRetorno.timeout: u'A Rede não respondeu ao chamado. Por favor, aguarde um momento e tente novamente.',
    StatusDeRetorno.erro_nos_dados: u'Uma ou mais informações enviadas não são válidas. Por favor, revise os seus dados e tente novamente.',
    StatusDeRetorno.erro_na_comunicacao: u'Ocorreu um erro de comunicação com a Rede. Por favor, tente de novo.',
    StatusDeRetorno.nao_autorizado: u'A compra não foi autorizada pela Rede. Por favor, use outro meio de pagamento.',
    StatusDeRetorno.fulfill_nao_executado: u'Houve uma tentativa de confirmação de uma transação que não pode ser confirmada ou que já foi confirmada.',
    StatusDeRetorno.tipo_cartao_invalido: u'Tipo de cartão inválido.',
    StatusDeRetorno.referencia_invalida: u'Os números de referência devem ter 16 dígitos para transações de fulfill, ou de 6 a 30 dígitos para todas as outras',
    StatusDeRetorno.data_expiracao_invalida: u'A data de expiração é inválida.',
    StatusDeRetorno.cartao_expirado: u'O cartão usado está expirado. Por favor, use outro cartão.',
    StatusDeRetorno.numero_cartao_invalido: u'O número do cartão é inválido.',
    StatusDeRetorno.numero_cartao_incompleto: u'O número do cartão está incompleto.',
    StatusDeRetorno.cartao_ainda_invalido: u'Cartão ainda não é válido',
    StatusDeRetorno.valor_invalido: u'Não foi enviado um valor de pagamento válido.',
    StatusDeRetorno.referencia_em_uso: u'Já existe uma transação no sistema com este número de referência.',
    StatusDeRetorno.cartao_usado_recentemente: u'Esse cartão foi usado recentemente. Por favor, aguarde um momento ou use um outro cartão.',
    StatusDeRetorno.xml_invalido: u'O XML está incorreto. O motivo é detalhado no elemento <information> de resposta da transação',
    StatusDeRetorno.erro_configuracao: u'Um erro na configuração de conta causou a falha da transação. Entre em contato com o suporte do e-Rede.',
    StatusDeRetorno.cv2_incompleto: u'O número CV2 deve ter 3 dígitos',
    StatusDeRetorno.estabelecimento_invalido_1: u'O ID da loja na Rede é inválido. Por favor, contacte o SAC da loja e informe o problema.',
    StatusDeRetorno.estabelecimento_invalido_2: u'O ID da loja na Rede é inválido. Por favor, contacte o SAC da loja e informe o problema.',
    StatusDeRetorno.tempo_limite_para_autorizacao: u'O tempo para autorizar essa transação passou do limite estabelecido. Por favor, refaça o pedido e tente novamente.',
    StatusDeRetorno.rsg_invalido: u'Serviço RSG inválido especificado'
}


class Ambiente(object):
    producao = 'P'
    homologacao = 'H'


class PassosDeEnvio(object):
    auth = 'auth'
    pre = 'pre'
    accept_review = 'accept_review'
    fulfill = 'fulfill'


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        if dados['passo'] == PassosDeEnvio.pre:
            self.servico = PreEnvio(loja_id, plano_indice, dados=dados)
        if dados['passo'] in [PassosDeEnvio.fulfill, PassosDeEnvio.accept_review]:
            self.servico = CompletaPagamento(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.servico.conexao = self.obter_conexao(formato_envio=requisicao.Formato.xml, formato_resposta=requisicao.Formato.xml)
        self.servico.url = 'https://api.pagar.me/1/transactions'

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
        raise self.EnvioNaoRealizado(u'Ocorreram erros no envio dos dados para o PAGAR.ME', self.loja_id, self.pedido.numero, dados_envio=self.malote.to_dict(), erros=self.servico.resposta.conteudo)


class PreEnvio(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(PreEnvio, self).__init__(loja_id, plano_indice, dados=dados)
        self.resposta = None
        self.conexao = None
        self.url = None
        self.status_retorno = None
        self.status_rejeicao = None

    def envia_pagamento(self, tentativa=1):
        self.resposta = self.conexao.post(self.url, self.malote.to_xml(raiz=True))

    def processa_dados_pagamento(self):
        self.dados_pagamento = {
            'transacao_id': self.resposta.conteudo['chave'],
            'valor_pago': self.pedido.valor_total,
            'conteudo_json': {
                'bandeira': self.resposta.conteudo['chave'],
                'aplicacao': self.configuracao.aplicacao
            }
        }
        if self.tem_parcelas:
            self.dados_pagamento['conteudo_json'].update({
                'numero_parcelas': int(self.dados['cartao_parcelas']),
                'valor_parcela': float(self.dados['cartao_valor_parcela']),
                'sem_juros': self.dados['cartao_parcelas_sem_juros'] == 'true'
            })
        self.identificacao_pagamento = self.resposta.conteudo['chave']

    @property
    def tem_parcelas(self):
        parcelas = self.dados.get('cartao_parcelas', 1)
        return int(parcelas) > 1


class CompletaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice, dados=None):
        super(CompletaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.conexao = None
        self.url = None
        self.resposta = None
        self.passo_atual = dados.get('passo', '')

    def envia_pagamento(self, tentativa=1):
        self.resposta = self.conexao.post(self.url, self.malote.to_xml(raiz=True))

    def processa_dados_pagamento(self):
        self.dados_pagamento = {
            'transacao_id': self.resposta.conteudo['chave'],
            'identificador_id': self.resposta.conteudo['chave'],
        }
        self.situacao_pedido = self._situacao_pedido

    @property
    def _situacao_pedido(self):
        if self.passo_atual == PassosDeEnvio.accept_review:
            return servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE
        if self.passo_atual == PassosDeEnvio.fulfill:
            return servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO
        return None

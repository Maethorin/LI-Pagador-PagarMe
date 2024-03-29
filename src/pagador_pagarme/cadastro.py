# -*- coding: utf-8 -*-

from li_common.padroes import cadastro
from li_common.comunicacao import requisicao


class AmbienteValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        resposta = requisicao.Conexao(formato_envio=requisicao.Formato.querystring).get('https://api.pagar.me/1/company', dados={'api_key': self.valores.get('token', '000')})
        if not resposta.sucesso:
            return True
        if self.valor == 'L':
            valido = resposta.conteudo['status'] == 'active'
            if not valido:
                self.erros = u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de atualizar na Loja Integrada.'
            return valido
        return True


class ChaveApiValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        resposta = requisicao.Conexao(formato_envio=requisicao.Formato.querystring).get('https://api.pagar.me/1/company', dados={'api_key': self.valor})
        if not resposta.sucesso:
            self.erros = u'A Chave de Api digitada não é válida. Se você está tentando usar a chave de api LIVE, altere sua loja para LIVE primeiro no Pagar.Me.'
            return False
        if self.valor.startswith('ak_live'):
            valido = resposta.conteudo['status'] == 'active'
            if not valido:
                self.erros = u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de usar a chave de api live.'
            return valido
        return True


class FormularioPagarMe(cadastro.Formulario):
    _PARCELAS = [(x, x) for x in range(1, 13)]

    ativo = cadastro.CampoFormulario('ativo', 'Pagamento ativo?', tipo=cadastro.TipoDeCampo.boleano, ordem=1)
    ambiente = cadastro.CampoFormulario('aplicacao', u'Ambiente', tipo=cadastro.TipoDeCampo.escolha, validador=AmbienteValidador, requerido=True, opcoes=(('T', u'test'), ('L', u'live')), ordem=2, texto_ajuda=u'Use test para validar sua integração com o PAGAR.ME. Ao alterar essa opção para live, você também deve alterar sua conta no PAGAR.ME para live.')
    chave_api = cadastro.CampoFormulario('token', u'Chave de API', requerido=True, tamanho_max=128, ordem=3, validador=ChaveApiValidador, texto_ajuda=u'Copie a chave do seu dashboard Pagar.me e cole aqui')
    chave_criptografia = cadastro.CampoFormulario('senha', u'Chave de criptografia', requerido=True, tamanho_max=128, ordem=4, texto_ajuda=u'Copie a chave do seu dashboard Pagar.me e cole aqui')
    complemento_fatura = cadastro.CampoFormulario('informacao_complementar', u'Complemento na Fatura do Comprador', tamanho_max=13, requerido=False, ordem=5, texto_ajuda=u'Complemento para exibir na fatura do comprador junto com o nome da loja configurado no Pagar.Me')
    valor_minimo_aceitado = cadastro.CampoFormulario('valor_minimo_aceitado', u'Valor mínimo', requerido=False, decimais=2, ordem=6, tipo=cadastro.TipoDeCampo.decimal, texto_ajuda=u'Informe o valor mínimo para exibir esta forma de pagamento.')
    valor_minimo_parcela = cadastro.CampoFormulario('valor_minimo_parcela', u'Valor mínimo da parcela', requerido=False, decimais=2, ordem=7, tipo=cadastro.TipoDeCampo.decimal)
    parcelas_sem_juros = cadastro.CampoFormulario('parcelas_sem_juros', 'Parcelas sem juros', tipo=cadastro.TipoDeCampo.escolha, requerido=False, ordem=8, texto_ajuda=u'Número de parcelas sem juros para esta forma de pagamento.', opcoes=_PARCELAS)
    maximo_parcelas = cadastro.CampoFormulario('maximo_parcelas', u'Máximo de parcelas', tipo=cadastro.TipoDeCampo.escolha, requerido=False, ordem=9, texto_ajuda=u'Quantidade máxima de parcelas para esta forma de pagamento.', opcoes=_PARCELAS)
    mostrar_parcelamento = cadastro.CampoFormulario('mostrar_parcelamento', u'Marque para mostrar o parcelamento na listagem e na página do produto.', tipo=cadastro.TipoDeCampo.boleano, requerido=False, ordem=10)

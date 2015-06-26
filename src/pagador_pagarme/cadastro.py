# -*- coding: utf-8 -*-

from li_common.padroes import cadastro


class BoletoValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        if type(self.valor) is not dict:
            self.erros['dados_invalidos'] = u'Os dados do boleto devem ser em formato de dicionário'
            return False
        if int(self.valor.get('dias_vencimento', 0) or 0) <= 0:
            self.erros['dias_vencimento'] = u'Dias para o vencimento deve ser maior que 0 (zero).'
        return not self.erros


class FormularioPagarMe(cadastro.Formulario):
    _PARCELAS = [(x, x) for x in range(1, 12)]
    _PARCELAS.insert(0, (12, 'Todas'))
    dados_boleto = cadastro.CampoFormulario('json', ordem=0, tipo=cadastro.TipoDeCampo.oculto, formato=cadastro.FormatoDeCampo.json, validador=BoletoValidador)

    ativo = cadastro.CampoFormulario('ativo', 'Pagamento ativo?', tipo=cadastro.TipoDeCampo.boleano, ordem=1)
    ambiente = cadastro.CampoFormulario('aplicacao', u'Ambiente', tipo=cadastro.TipoDeCampo.escolha, requerido=True, opcoes=(('T', u'test'), ('L', u'live')), ordem=2, texto_ajuda=u'Use test para validar sua integração com o PAGAR.ME. Ao alterar essa opção para live, você também deve alterar sua conta no PAGAR.ME para live.')
    chave_api = cadastro.CampoFormulario('token', u'Chave de API', requerido=True, tamanho_max=128, ordem=3, texto_ajuda=u'Copie a chave do seu dashboard Pagar.me e cole aqui')
    chave_criptografia = cadastro.CampoFormulario('senha', u'Chave de criptografia', requerido=True, tamanho_max=128, ordem=4, texto_ajuda=u'Copie a chave do seu dashboard Pagar.me e cole aqui')
    valor_minimo_aceitado = cadastro.CampoFormulario('valor_minimo_aceitado', u'Valor mínimo', requerido=False, decimais=2, ordem=5, tipo=cadastro.TipoDeCampo.decimal, texto_ajuda=u'Informe o valor mínimo para exibir esta forma de pagamento.')
    valor_minimo_parcela = cadastro.CampoFormulario('valor_minimo_parcela', u'Valor mínimo da parcela', requerido=False, decimais=2, ordem=6, tipo=cadastro.TipoDeCampo.decimal)
    parcelas_sem_juros = cadastro.CampoFormulario('parcelas_sem_juros', 'Parcelas sem juros', tipo=cadastro.TipoDeCampo.escolha, requerido=False, ordem=7, texto_ajuda=u'Número de parcelas sem juros para esta forma de pagamento.', opcoes=_PARCELAS)
    mostrar_parcelamento = cadastro.CampoFormulario('mostrar_parcelamento', u'Marque para mostrar o parcelamento na listagem e na página do produto.', tipo=cadastro.TipoDeCampo.boleano, requerido=False, ordem=8)

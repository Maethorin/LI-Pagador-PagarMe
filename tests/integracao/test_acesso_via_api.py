# -*- coding: utf-8 -*-
import json
import mock
from li_common.padroes import extensibilidade

from tests.base import TestBase

extensibilidade.SETTINGS.EXTENSOES = {
    'pagarme': 'pagador_pagarme'
}


class PagarMeConfiguracaoMeioDePagamentoDaLoja(TestBase):
    url = '/loja/8/meio-pagamento/pagarme/configurar'

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento')
    def test_deve_obter_dados_pagarme(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.to_dict.return_value = 'PAGAR.ME'
        response = self.app.get(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'configuracao_pagamento': u'PAGAR.ME'}})
        response.status_code.should.be.equal(200)
        configuracao_mock.assert_called_with(loja_id=8, codigo_pagamento='pagarme')

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento')
    def test_deve_grava_dados_pagarme(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.to_dict.return_value = 'PAGAR.ME'
        response = self.app.post(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'configuracao_pagamento': u'PAGAR.ME'}})
        response.status_code.should.be.equal(200)
        configuracao.salvar_formulario.assert_called_with({'token': u'ZES'})


class PagarMeEnviandoPagamento(TestBase):
    url = '/loja/8/meio-pagamento/pagarme/enviar/1234/1'

    @mock.patch('pagador.servicos.GerenciaPedido', mock.MagicMock())
    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador_pagarme.servicos.EntregaPagamento')
    def test_deve_enviar_pagamento(self, entrega_mock):
        entrega_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'pagamento-enviado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'zas': u'pagamento-enviado'}})


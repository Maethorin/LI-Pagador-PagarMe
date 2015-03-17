# -*- coding: utf-8 -*-
import unittest

import mock

from pagador_pagarme import entidades


class PagarMeConfiguracaoMeioPagamento(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PagarMeConfiguracaoMeioPagamento, self).__init__(*args, **kwargs)
        self.campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
        self.codigo_gateway = 12

    def test_deve_ter_os_campos_especificos_na_classe(self):
        entidades.ConfiguracaoMeioPagamento._campos.should.be.equal(self.campos)

    def test_deve_ter_codigo_gateway(self):
        entidades.ConfiguracaoMeioPagamento._codigo_gateway.should.be.equal(self.codigo_gateway)

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_preencher_gateway_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        preencher_mock.assert_called_with(configuracao, self.codigo_gateway, self.campos)

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_definir_formulario_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.formulario.should.be.a('pagador_pagarme.cadastro.FormularioPagarMe')

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_ser_aplicacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_aplicacao.should.be.falsy

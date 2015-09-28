# -*- coding: utf-8 -*-
import unittest
import mock

from pagador_pagarme import cadastro


class FormularioPagarMe(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FormularioPagarMe, self).__init__(*args, **kwargs)
        self.formulario = cadastro.FormularioPagarMe()

    def test_deve_ter_ativo(self):
        self.formulario.ativo.nome.should.be.equal('ativo')
        self.formulario.ativo.ordem.should.be.equal(1)
        self.formulario.ativo.label.should.be.equal('Pagamento ativo?')
        self.formulario.ativo.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.boleano)

    def test_deve_ter_ambiente(self):
        self.formulario.ambiente.nome.should.be.equal('aplicacao')
        self.formulario.ambiente.ordem.should.be.equal(2)
        self.formulario.ambiente.label.should.be.equal(u'Ambiente')
        self.formulario.ambiente.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.escolha)
        self.formulario.ambiente.opcoes.should.be.equal((('T', u'test'), ('L', u'live')))

    def test_deve_ter_chave_api(self):
        self.formulario.chave_api.nome.should.be.equal('token')
        self.formulario.chave_api.ordem.should.be.equal(3)
        self.formulario.chave_api.label.should.be.equal(u'Chave de API')
        self.formulario.chave_api.tamanho_max.should.be.equal(128)
        self.formulario.chave_api.requerido.should.be.truthy

    def test_deve_ter_chave_criptografica(self):
        self.formulario.chave_criptografia.nome.should.be.equal('senha')
        self.formulario.chave_criptografia.ordem.should.be.equal(4)
        self.formulario.chave_criptografia.label.should.be.equal(u'Chave de criptografia')
        self.formulario.chave_criptografia.tamanho_max.should.be.equal(128)
        self.formulario.chave_criptografia.requerido.should.be.truthy

    def test_deve_ter_complemento_fatura(self):
        self.formulario.complemento_fatura.nome.should.be.equal('informacao_complementar')
        self.formulario.complemento_fatura.ordem.should.be.equal(5)
        self.formulario.complemento_fatura.label.should.be.equal(u'Complemento na Fatura do Comprador')
        self.formulario.complemento_fatura.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.texto)

    def test_deve_ter_valor_minimo_aceitado(self):
        self.formulario.valor_minimo_aceitado.nome.should.be.equal('valor_minimo_aceitado')
        self.formulario.valor_minimo_aceitado.ordem.should.be.equal(6)
        self.formulario.valor_minimo_aceitado.label.should.be.equal(u'Valor mínimo')
        self.formulario.valor_minimo_aceitado.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.decimal)

    def test_deve_ter_valor_minimo_parcela(self):
        self.formulario.valor_minimo_parcela.nome.should.be.equal('valor_minimo_parcela')
        self.formulario.valor_minimo_parcela.ordem.should.be.equal(7)
        self.formulario.valor_minimo_parcela.label.should.be.equal(u'Valor mínimo da parcela')
        self.formulario.valor_minimo_parcela.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.decimal)

    def test_deve_ter_parcelas_sem_juros(self):
        self.formulario.parcelas_sem_juros.nome.should.be.equal('parcelas_sem_juros')
        self.formulario.parcelas_sem_juros.ordem.should.be.equal(8)
        self.formulario.parcelas_sem_juros.label.should.be.equal('Parcelas sem juros')
        self.formulario.parcelas_sem_juros.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.escolha)

    def test_deve_ter_maximo_parcelas(self):
        self.formulario.maximo_parcelas.nome.should.be.equal('maximo_parcelas')
        self.formulario.maximo_parcelas.ordem.should.be.equal(9)
        self.formulario.maximo_parcelas.label.should.be.equal(u'Máximo de parcelas')
        self.formulario.maximo_parcelas.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.escolha)

    def test_deve_ter_mostrar_parcelamento(self):
        self.formulario.mostrar_parcelamento.nome.should.be.equal('mostrar_parcelamento')
        self.formulario.mostrar_parcelamento.ordem.should.be.equal(10)
        self.formulario.mostrar_parcelamento.label.should.be.equal(u'Marque para mostrar o parcelamento na listagem e na página do produto.')
        self.formulario.mostrar_parcelamento.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.boleano)

    def test_deve_ter_quantidade_certa_parcelas(self):
        self.formulario._PARCELAS.should.be.equal([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12)])


class ValidarAmbiente(unittest.TestCase):
    @mock.patch('pagador_pagarme.cadastro.requisicao.Conexao')
    def test_nao_deve_validar_live_com_test_no_pagarme(self, conexao_mock):
        conexao_mock.return_value.get.return_value = mock.MagicMock(sucesso=True, conteudo={'status': 'nao'})
        validador = cadastro.AmbienteValidador(valor='L', valores={'token': 'zas'})
        validador.eh_valido.should.be.falsy
        validador.erros.should.be.equal(u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de atualizar na Loja Integrada.')
        conexao_mock.assert_called_with(formato_envio='text/html')
        conexao_mock.return_value.get.assert_called_with('https://api.pagar.me/1/company', dados={'api_key': 'zas'})

    @mock.patch('pagador_pagarme.cadastro.requisicao.Conexao')
    def test_deve_validar_live_com_live_no_pagarme(self, conexao_mock):
        conexao_mock.return_value.get.return_value = mock.MagicMock(sucesso=True, conteudo={'status': 'active'})
        validador = cadastro.AmbienteValidador(valor='L', valores={'token': 'zas'})
        validador.eh_valido.should.be.truthy
        validador.erros.should.be.empty


class ValidarChaveApi(unittest.TestCase):
    @mock.patch('pagador_pagarme.cadastro.requisicao.Conexao')
    def test_nao_deve_validar_live_com_erro_no_pagarme(self, conexao_mock):
        conexao_mock.return_value.get.return_value = mock.MagicMock(sucesso=False)
        validador = cadastro.ChaveApiValidador(valor='zas', valores={})
        validador.eh_valido.should.be.falsy
        validador.erros.should.be.equal(u'A Chave de Api digitada não é válida. Se você está tentando usar a chave de api LIVE, altere sua loja para LIVE primeiro no Pagar.Me.')
        conexao_mock.assert_called_with(formato_envio='text/html')
        conexao_mock.return_value.get.assert_called_with('https://api.pagar.me/1/company', dados={'api_key': 'zas'})

    @mock.patch('pagador_pagarme.cadastro.requisicao.Conexao')
    def test_nao_deve_validar_live_com_teste_no_pagarme(self, conexao_mock):
        conexao_mock.return_value.get.return_value = mock.MagicMock(sucesso=True, conteudo={'status': 'nao'})
        validador = cadastro.ChaveApiValidador(valor='ak_live_zas', valores={})
        validador.eh_valido.should.be.falsy
        validador.erros.should.be.equal(u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de usar a chave de api live.')

    @mock.patch('pagador_pagarme.cadastro.requisicao.Conexao')
    def test_deve_validar_live_com_live_no_pagarme(self, conexao_mock):
        conexao_mock.return_value.get.return_value = mock.MagicMock(sucesso=True, conteudo={'status': 'active'})
        validador = cadastro.ChaveApiValidador(valor='ak_live_zas', valores={})
        validador.eh_valido.should.be.truthy
        validador.erros.should.be.empty

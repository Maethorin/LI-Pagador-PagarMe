# -*- coding: utf-8 -*-
import unittest
from decimal import Decimal

import mock

from pagador_pagarme import entidades


class PagarMeConfiguracaoMeioPagamento(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PagarMeConfiguracaoMeioPagamento, self).__init__(*args, **kwargs)
        self.campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
        self.codigo_gateway = 12

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_os_campos_especificos_na_classe(self):
        entidades.ConfiguracaoMeioPagamento(234).campos.should.be.equal(self.campos)

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_codigo_gateway(self):
        entidades.ConfiguracaoMeioPagamento(234).codigo_gateway.should.be.equal(self.codigo_gateway)

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_preencher_gateway_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        preencher_mock.assert_called_with(configuracao, self.codigo_gateway, self.campos)

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_definir_formulario_na_inicializacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.formulario.should.be.a('pagador_pagarme.cadastro.FormularioPagarMe')

    @mock.patch('pagador_pagarme.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ser_aplicacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_aplicacao.should.be.falsy


class PagarMeMontandoMalote(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(PagarMeMontandoMalote, self).__init__(methodName)
        self.pedido = mock.MagicMock(
            numero=123,
            valor_total=Decimal('14.00'),
            cliente={
                'nome': 'Cliente Teste',
                'email': 'email@cliente.com',
            },
            cliente_documento='12345678901',
            cliente_telefone=('11', '23456789'),
            endereco_cliente={
                'endereco': 'Rua Teste',
                'numero': 123,
                'complemento': 'Apt 101',
                'bairro': 'Teste',
                'cep': '10234000'
            },
            itens=[
                entidades.entidades.ItemDePedido(nome='Produto 1', sku='PROD01', quantidade=1, preco_venda=Decimal('40.00')),
                entidades.entidades.ItemDePedido(nome='Produto 2', sku='PROD02', quantidade=1, preco_venda=Decimal('50.00')),
            ],
            conteudo_json={
                'pagarme': {
                    'nome_loja': 'Nome Loja',
                    'cartao':  'cartao-hash',
                    'parcelas':  1,
                    'parcelas_sem_juros':  'false',
                    'valor_parcela':  None,
                }
            }
        )

    def test_malote_deve_ter_propriedades(self):
        entidades.Malote('configuracao').to_dict().should.be.equal({'amount': None, 'capture': 'true', 'customer': None, 'card_hash': None, 'free_installments': None, 'installments': None, 'payment_method': 'credit_card', 'metadata': None, 'postback_url': None})

    def test_deve_montar_conteudo_sem_parcelas(self):
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, {})
        malote.to_dict().should.be.equal({'amount': 1400, 'capture': 'true', 'card_hash': 'cartao-hash', 'customer': {'address': {'complementary': 'Apt 101', 'neighborhood': 'Teste', 'street': 'Rua Teste', 'street_number': 123, 'zipcode': '10234000'}, 'document_number': '12345678901', 'email': 'email@cliente.com', 'name': 'Cliente Teste', 'phone': {'ddd': '11', 'number': '23456789'}}, 'installments': 1, 'metadata': {'carrinho': [{'nome': 'Produto 1', 'preco_venda': 40.0, 'quantidade': 1, 'sku': 'PROD01'}, {'nome': 'Produto 2', 'preco_venda': 50.0, 'quantidade': 1, 'sku': 'PROD02'}], 'pedido_numero': 123}, 'payment_method': 'credit_card', 'postback_url': 'http://localhost:5000/pagador/meio-pagamento/pagarme/retorno/8/notificacao?referencia=123'})

    def test_deve_montar_conteudo_com_parcelas_sem_juros(self):
        self.pedido.conteudo_json['pagarme']['parcelas'] = 3
        self.pedido.conteudo_json['pagarme']['parcelas_sem_juros'] = 'true'
        self.pedido.conteudo_json['pagarme']['valor_parcela'] = '12.98'
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, {})
        malote.to_dict().should.be.equal({'amount': 1400, 'capture': 'true', 'card_hash': 'cartao-hash', 'customer': {'address': {'complementary': 'Apt 101', 'neighborhood': 'Teste', 'street': 'Rua Teste', 'street_number': 123, 'zipcode': '10234000'}, 'document_number': '12345678901', 'email': 'email@cliente.com', 'name': 'Cliente Teste', 'phone': {'ddd': '11', 'number': '23456789'}}, 'free_installments': 3, 'metadata': {'carrinho': [{'nome': 'Produto 1', 'preco_venda': 40.0, 'quantidade': 1, 'sku': 'PROD01'}, {'nome': 'Produto 2', 'preco_venda': 50.0, 'quantidade': 1, 'sku': 'PROD02'}], 'pedido_numero': 123}, 'payment_method': 'credit_card', 'postback_url': 'http://localhost:5000/pagador/meio-pagamento/pagarme/retorno/8/notificacao?referencia=123'})

    def test_deve_montar_conteudo_com_parcelas_com_juros(self):
        self.pedido.conteudo_json['pagarme']['parcelas'] = 3
        self.pedido.conteudo_json['pagarme']['parcelas_sem_juros'] = 'false'
        self.pedido.conteudo_json['pagarme']['valor_parcela'] = '12.98'
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, {})
        malote.to_dict().should.be.equal({'amount': 1400, 'capture': 'true', 'card_hash': 'cartao-hash', 'customer': {'address': {'complementary': 'Apt 101', 'neighborhood': 'Teste', 'street': 'Rua Teste', 'street_number': 123, 'zipcode': '10234000'}, 'document_number': '12345678901', 'email': 'email@cliente.com', 'name': 'Cliente Teste', 'phone': {'ddd': '11', 'number': '23456789'}}, 'installments': 3, 'payment_method': 'credit_card', 'metadata': {'carrinho': [{'nome': 'Produto 1', 'preco_venda': 40.0, 'quantidade': 1, 'sku': 'PROD01'}, {'nome': 'Produto 2', 'preco_venda': 50.0, 'quantidade': 1, 'sku': 'PROD02'}], 'pedido_numero': 123}, 'postback_url': 'http://localhost:5000/pagador/meio-pagamento/pagarme/retorno/8/notificacao?referencia=123'})

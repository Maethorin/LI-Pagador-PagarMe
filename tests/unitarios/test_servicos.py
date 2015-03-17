# -*- coding: utf-8 -*-
import unittest
import mock
from pagador_pagarme import servicos


class PagarMeCredenciais(unittest.TestCase):
    def test_deve_definir_propriedades(self):
        credenciador = servicos.Credenciador(configuracao=mock.MagicMock())
        credenciador.tipo.should.be.equal(credenciador.TipoAutenticacao.form_urlencode)
        credenciador.chave.should.be.equal('api_key')

    def test_deve_retornar_credencial_baseado_no_usuario(self):
        configuracao = mock.MagicMock(token='api-key')
        credenciador = servicos.Credenciador(configuracao=configuracao)
        credenciador.obter_credenciais().should.be.equal('api-key')


class PagarMeSituacoesPagamento(unittest.TestCase):
    def test_deve_retornar_pago_para_paid(self):
        servicos.SituacoesDePagamento.do_tipo('paid').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_retornar_cancelado_para_refused(self):
        servicos.SituacoesDePagamento.do_tipo('refused').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO)

    def test_deve_retornar_none_para_desconhecido(self):
        servicos.SituacoesDePagamento.do_tipo('zas').should.be.none


class PagarMeEntregaPagamento(unittest.TestCase):
    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_tem_malote(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.tem_malote.should.be.truthy

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_faz_http(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.faz_http.should.be.truthy

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagarme.servicos.PreEnvio')
    def test_pre_instancia_pre_envio(self, pre_envio_mock):
        pre_envio = mock.MagicMock()
        pre_envio_mock.return_value = pre_envio
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.should.be.equal(pre_envio)
        pre_envio_mock.assert_called_with(1234, 1, dados={'passo': 'pre'})

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagarme.servicos.CompletaPagamento')
    def test_pre_instancia_pre_envio(self, completa_pagamento_mock):
        completa_pagamento = mock.MagicMock()
        completa_pagamento_mock.return_value = completa_pagamento
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'captura'})
        entregador.servico.should.be.equal(completa_pagamento)
        completa_pagamento_mock.assert_called_with(1234, 1, dados={'passo': 'captura'})

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_resposta(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.resposta.should.be.none

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_url(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.url.should.be.equal('https://api.pagar.me/1/transactions')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao')
    def test_deve_montar_conexao(self, obter_mock):
        obter_mock.return_value = 'conexao'
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.conexao.should.be.equal('conexao')
        obter_mock.assert_called_with(formato_envio='application/x-www-form-urlencoded')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagarme.servicos.Credenciador')
    def test_deve_definir_credenciais(self, credenciador_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        credenciador_mock.return_value = 'credenciador'
        entregador.configuracao = 'configuracao'
        entregador.define_credenciais()
        entregador.servico.conexao.credenciador.should.be.equal('credenciador')
        credenciador_mock.assert_called_with(configuracao='configuracao')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador.servicos.EntregaPagamento.define_pedido_e_configuracao')
    def test_deve_definir_configuracao_e_pedido_de_servico(self, define_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.configuracao = 'configuracao'
        entregador.pedido = 'pedido'
        entregador.define_pedido_e_configuracao(1234)
        define_mock.assert_called_with(1234)
        entregador.servico.configuracao.should.be.equal('configuracao')
        entregador.servico.pedido.should.be.equal('pedido')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador.servicos.EntregaPagamento.montar_malote')
    def test_deve_montar_malote_de_servico(self, montar_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.malote = 'malote'
        entregador.montar_malote()
        montar_mock.assert_called_with()
        entregador.servico.malote.should.be.equal('malote')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.malote = mock.MagicMock()
        entregador.servico.malote.to_dict.return_value = 'malote-como-dicionario'
        entregador.servico.conexao = mock.MagicMock()
        entregador.servico.conexao.post.return_value = 'resposta'
        entregador.envia_pagamento()
        entregador.dados_enviados.should.be.equal('malote-como-dicionario')
        entregador.resposta.should.be.equal('resposta')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_usar_post_ao_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.malote = mock.MagicMock()
        entregador.servico.malote.to_dict.return_value = 'malote-como-dicionario'
        entregador.servico.conexao = mock.MagicMock()
        entregador.envia_pagamento()
        entregador.servico.conexao.post.assert_called_with(entregador.servico.url, 'malote-como-dicionario')

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_nao_tem_parcelas_sem_cartao_parcelas_em_dados(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico.tem_parcelas.should.be.falsy

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_nao_tem_parcelas_comm_cartao_parcelas_igual_a_um(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre', 'cartao_parcelas': 1})
        entregador.servico.tem_parcelas.should.be.falsy

    @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_tem_parcelas_comm_cartao_parcelas_maior_que_um(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre', 'cartao_parcelas': 3})
        entregador.servico.tem_parcelas.should.be.truthy

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_dados_de_pagamento(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador._processa_resposta = mock.MagicMock()
    #     entregador._processa_resposta.return_value = 'resposta-processada'
    #     entregador.processa_dados_pagamento()
    #     entregador._processa_resposta.assert_called_with()
    #     entregador.resultado.should.be.equal('resposta-processada')

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_resposta_sucesso(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.resposta = mock.MagicMock(conteudo={'checkout': {'code': 'code-checkout'}}, status_code=200, sucesso=True, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False)
    #     entregador.processa_dados_pagamento()
    #     entregador.resultado.should.be.equal({'url': 'https://sandbox.pagarme.uol.com.br/v2/checkout/payment.html?code=code-checkout'})

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_resposta_erro(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.resposta = mock.MagicMock(conteudo={}, status_code=500, sucesso=False, erro_servidor=True, timeout=False, nao_autenticado=False, nao_autorizado=False)
    #     entregador.processa_dados_pagamento()
    #     entregador.resultado.should.be.equal({'mensagem': u'O servidor do PagarMe está indisponível nesse momento.', 'status_code': 500})

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_resposta_timeout(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.resposta = mock.MagicMock(conteudo={}, status_code=408, sucesso=False, erro_servidor=False, timeout=True, nao_autenticado=False, nao_autorizado=False)
    #     entregador.processa_dados_pagamento()
    #     entregador.resultado.should.be.equal({'mensagem': u'O servidor do PagarMe não respondeu em tempo útil.', 'status_code': 408})

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_resposta_nao_autenticado(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.resposta = mock.MagicMock(conteudo={}, status_code=401, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=True, nao_autorizado=False)
    #     entregador.processa_dados_pagamento()
    #     entregador.resultado.should.be.equal({'mensagem': u'Autenticação da loja com o PagarMe Falhou. Contate o SAC da loja.', 'status_code': 401})

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_processar_resposta_nao_autorizado(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.resposta = mock.MagicMock(conteudo={}, status_code=400, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=True)
    #     entregador.processa_dados_pagamento()
    #     entregador.resultado.should.be.equal({'mensagem': u'Autenticação da loja com o PagarMe Falhou. Contate o SAC da loja.', 'status_code': 400})

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_disparar_erro_se_resposta_vier_com_status_nao_conhecido_e_sem_erro(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.pedido = mock.MagicMock(numero=123)
    #     entregador.malote = mock.MagicMock()
    #     entregador.malote.to_dict.return_value = 'malote'
    #     entregador.resposta = mock.MagicMock(conteudo={'erro': 'zas'}, status_code=666, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False)
    #     entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_disparar_erro_se_tiver_erro_na_reposta(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.pedido = mock.MagicMock(numero=123)
    #     entregador.malote = mock.MagicMock()
    #     entregador.malote.to_dict.return_value = 'malote'
    #     entregador.resposta = mock.MagicMock(
    #         conteudo={
    #             'errors': {'error': {'code': 'code1', 'message': 'message1'}}
    #         },
    #         status_code=500, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False
    #     )
    #     entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)

    # @mock.patch('pagador_pagarme.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    # def test_deve_disparar_erro_se_tiver_lista_de_erros_na_reposta(self):
    #     entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
    #     entregador.pedido = mock.MagicMock(numero=123)
    #     entregador.malote = mock.MagicMock()
    #     entregador.malote.to_dict.return_value = 'malote'
    #     entregador.resposta = mock.MagicMock(
    #         conteudo={
    #             'errors': [
    #                 {'error': {'code': 'code1', 'message': 'message1'}},
    #                 {'error': {'code': 'code2', 'message': 'message2'}}
    #             ]
    #         },
    #         status_code=500, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False
    #     )
    #     entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)


class PreEnviandoPagamento(unittest.TestCase):
    def test_tem_conexao(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.conexao.should.be.none

    def test_tem_url(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.url.should.be.none

    def test_tem_entrega(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.entrega.should.be.none

    def test_envia_post_define_dados_da_entrega(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.entrega = mock.MagicMock()
        pre_envio.conexao = mock.MagicMock()
        pre_envio.malote = mock.MagicMock()
        pre_envio.malote.to_dict.return_value = 'malote'
        pre_envio.envia_pagamento()
        pre_envio.entrega.dados_enviados.should.be.equal('malote')

    def test_envia_post_define_resposta_da_entrega(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.entrega = mock.MagicMock()
        pre_envio.conexao = mock.MagicMock()
        pre_envio.conexao.post.return_value = 'resposta'
        pre_envio.malote = mock.MagicMock()
        pre_envio.malote.to_dict.return_value = 'malote'
        pre_envio.envia_pagamento()
        pre_envio.entrega.resposta.should.be.equal('resposta')

    def test_envia_post_chama_post_de_conexao(self):
        pre_envio = servicos.PreEnvio(1234)
        pre_envio.entrega = mock.MagicMock()
        pre_envio.conexao = mock.MagicMock()
        pre_envio.url = 'url-envio'
        pre_envio.malote = mock.MagicMock()
        pre_envio.malote.to_dict.return_value = 'malote'
        pre_envio.envia_pagamento()
        pre_envio.conexao.post.assert_called_with('url-envio', 'malote')


class CompletandoPagamento(unittest.TestCase):
    def test_tem_conexao(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.conexao.should.be.none

    def test_tem_url(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.url.should.be.none

    def test_tem_entrega(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.entrega.should.be.none

    def test_envia_post_define_dados_da_entrega(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.entrega = mock.MagicMock()
        completa_pagamento.conexao = mock.MagicMock()
        completa_pagamento.malote = mock.MagicMock()
        completa_pagamento.malote.to_dict.return_value = 'malote'
        completa_pagamento.envia_pagamento()
        completa_pagamento.entrega.dados_enviados.should.be.equal('malote')

    def test_envia_post_define_resposta_da_entrega(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.entrega = mock.MagicMock()
        completa_pagamento.conexao = mock.MagicMock()
        completa_pagamento.conexao.post.return_value = 'resposta'
        completa_pagamento.malote = mock.MagicMock()
        completa_pagamento.malote.to_dict.return_value = 'malote'
        completa_pagamento.envia_pagamento()
        completa_pagamento.entrega.resposta.should.be.equal('resposta')

    def test_envia_post_chama_post_de_conexao(self):
        completa_pagamento = servicos.CompletaPagamento(1234)
        completa_pagamento.entrega = mock.MagicMock()
        completa_pagamento.conexao = mock.MagicMock()
        completa_pagamento.url = 'url-envio'
        completa_pagamento.malote = mock.MagicMock()
        completa_pagamento.malote.to_dict.return_value = 'malote'
        completa_pagamento.envia_pagamento()
        completa_pagamento.conexao.post.assert_called_with('url-envio', 'malote')

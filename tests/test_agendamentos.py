import threading

import pytest


def criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T10:00", responsavel="Maria"):
    return client.post(
        "/agendamentos",
        json={"sala_id": sala_id, "responsavel": responsavel, "data_inicio": inicio, "data_fim": fim},
    )


class TestListagem:
    def test_get_salas_retorna_salas_cadastradas(self, client):
        resp = client.get("/salas")
        assert resp.status_code == 200
        nomes = {s["nome"] for s in resp.get_json()}
        assert {"Sala Teste", "Sala Grande"} <= nomes

    def test_get_agendamentos_por_sala_vazio(self, client, sala_id):
        resp = client.get(f"/salas/{sala_id}/agendamentos")
        assert resp.status_code == 200
        assert resp.get_json() == []


class TestCriacao:
    def test_cria_agendamento_valido(self, client, sala_id):
        resp = criar_agendamento(client, sala_id)
        assert resp.status_code == 201
        corpo = resp.get_json()
        assert corpo["sala_id"] == sala_id
        assert corpo["responsavel"] == "Maria"

    def test_rejeita_fim_antes_do_inicio(self, client, sala_id):
        resp = criar_agendamento(client, sala_id, inicio="2026-09-01T10:00", fim="2026-09-01T09:00")
        assert resp.status_code == 400

    def test_rejeita_fim_igual_ao_inicio(self, client, sala_id):
        resp = criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T09:00")
        assert resp.status_code == 400

    @pytest.mark.parametrize("campo", ["sala_id", "responsavel", "data_inicio", "data_fim"])
    def test_rejeita_payload_com_campo_faltando_sem_quebrar(self, client, sala_id, campo):
        payload = {
            "sala_id": sala_id,
            "responsavel": "Maria",
            "data_inicio": "2026-09-01T09:00",
            "data_fim": "2026-09-01T10:00",
        }
        del payload[campo]
        resp = client.post("/agendamentos", json=payload)
        assert resp.status_code == 400
        assert "mensagem" in resp.get_json()

    def test_rejeita_responsavel_vazio(self, client, sala_id):
        resp = criar_agendamento(client, sala_id, responsavel="   ")
        assert resp.status_code == 400

    def test_rejeita_data_com_formato_invalido(self, client, sala_id):
        resp = criar_agendamento(client, sala_id, inicio="nao-e-uma-data")
        assert resp.status_code == 400

    def test_rejeita_sala_inexistente(self, client):
        resp = criar_agendamento(client, sala_id=999999)
        assert resp.status_code == 404

    def test_rejeita_corpo_sem_json(self, client):
        resp = client.post("/agendamentos", data="isso nao e json", content_type="text/plain")
        assert resp.status_code == 400

    def test_bloqueia_conflito_de_horario(self, client, sala_id):
        criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T10:00")
        resp = criar_agendamento(client, sala_id, inicio="2026-09-01T09:30", fim="2026-09-01T10:30")
        assert resp.status_code == 409

    def test_permite_horarios_adjacentes_sem_sobreposicao(self, client, sala_id):
        criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T10:00")
        resp = criar_agendamento(client, sala_id, inicio="2026-09-01T10:00", fim="2026-09-01T11:00")
        assert resp.status_code == 201


class TestAtualizacao:
    def test_atualiza_agendamento_valido(self, client, sala_id):
        criado = criar_agendamento(client, sala_id).get_json()
        resp = client.put(
            f"/agendamentos/{criado['id']}",
            json={
                "sala_id": sala_id,
                "responsavel": "Joao",
                "data_inicio": "2026-09-01T11:00",
                "data_fim": "2026-09-01T12:00",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["responsavel"] == "Joao"

    def test_bloqueia_conflito_ao_editar_para_horario_ocupado(self, client, sala_id):
        criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T10:00")
        segundo = criar_agendamento(client, sala_id, inicio="2026-09-01T11:00", fim="2026-09-01T12:00").get_json()

        resp = client.put(
            f"/agendamentos/{segundo['id']}",
            json={
                "sala_id": sala_id,
                "responsavel": "Joao",
                "data_inicio": "2026-09-01T09:30",
                "data_fim": "2026-09-01T10:30",
            },
        )
        assert resp.status_code == 409

    def test_nao_conflita_com_ele_mesmo(self, client, sala_id):
        criado = criar_agendamento(client, sala_id, inicio="2026-09-01T09:00", fim="2026-09-01T10:00").get_json()
        resp = client.put(
            f"/agendamentos/{criado['id']}",
            json={
                "sala_id": sala_id,
                "responsavel": "Maria",
                "data_inicio": "2026-09-01T09:00",
                "data_fim": "2026-09-01T10:30",
            },
        )
        assert resp.status_code == 200

    def test_rejeita_payload_invalido_sem_quebrar(self, client, sala_id):
        criado = criar_agendamento(client, sala_id).get_json()
        resp = client.put(f"/agendamentos/{criado['id']}", json={"responsavel": "Joao"})
        assert resp.status_code == 400

    def test_agendamento_inexistente_retorna_404(self, client, sala_id):
        resp = client.put(
            "/agendamentos/999999",
            json={
                "sala_id": sala_id,
                "responsavel": "Joao",
                "data_inicio": "2026-09-01T09:00",
                "data_fim": "2026-09-01T10:00",
            },
        )
        assert resp.status_code == 404


class TestExclusao:
    def test_deleta_agendamento_existente(self, client, sala_id):
        criado = criar_agendamento(client, sala_id).get_json()
        resp = client.delete(f"/agendamentos/{criado['id']}")
        assert resp.status_code == 200
        assert client.get("/agendamentos").get_json() == []

    def test_deletar_inexistente_retorna_404(self, client):
        resp = client.delete("/agendamentos/999999")
        assert resp.status_code == 404


class TestConcorrencia:
    def test_duas_criacoes_simultaneas_no_mesmo_horario_so_uma_vence(self, app, sala_id):
        payload = {
            "sala_id": sala_id,
            "responsavel": "Concorrente",
            "data_inicio": "2026-09-01T14:00",
            "data_fim": "2026-09-01T15:00",
        }
        resultados = {}
        barreira = threading.Barrier(2)

        def tentar_criar(nome_thread):
            cliente_local = app.test_client()
            barreira.wait()
            resp = cliente_local.post("/agendamentos", json=payload)
            resultados[nome_thread] = resp.status_code

        t1 = threading.Thread(target=tentar_criar, args=("a",))
        t2 = threading.Thread(target=tentar_criar, args=("b",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        codigos = sorted(resultados.values())
        assert codigos == [201, 409], f"esperado exatamente uma vitoria e um conflito, obtive {resultados}"

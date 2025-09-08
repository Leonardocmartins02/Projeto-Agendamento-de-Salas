const API_URL = 'http://127.0.0.1:5000';

// --- Captura de Elementos ---
const listaSalasElement = document.getElementById('lista-salas');
const listaAgendamentosElement = document.getElementById('lista-agendamentos');
const salaSelecionadaTituloElement = document.getElementById('sala-selecionada-titulo');
const novoAgendamentoContainer = document.getElementById('novo-agendamento-container');
const formAgendamento = document.getElementById('form-novo-agendamento');
const salaIdHiddenInput = document.getElementById('sala_id_hidden');
const responsavelInput = document.getElementById('responsavel');
const dataInicioInput = document.getElementById('data_inicio');
const dataFimInput = document.getElementById('data_fim');
const painelMensagens = document.getElementById('painel-mensagens');
const botaoSubmit = formAgendamento.querySelector('button[type="submit"]');
const botaoCancelarEdicao = document.getElementById('botao-cancelar-edicao');

// --- Variáveis de Estado ---
let salaSelecionadaGlobal = null;
let agendamentoEmEdicaoId = null;

// --- Funções ---

function formatarDataHora(dataISO) {
    const data = new Date(dataISO);
    const dia = String(data.getDate()).padStart(2, '0');
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const ano = data.getFullYear();
    const hora = String(data.getHours()).padStart(2, '0');
    const minuto = String(data.getMinutes()).padStart(2, '0');
    return `${dia}/${mes}/${ano}, ${hora}:${minuto}`;
}

function mostrarMensagem(mensagem, tipo) {
    painelMensagens.textContent = mensagem;
    painelMensagens.className = tipo === 'sucesso' ? 'mensagem-sucesso' : 'mensagem-erro';
    setTimeout(() => { painelMensagens.className = ''; }, 4000);
}

async function carregarSalas() {
    try {
        const response = await fetch(`${API_URL}/salas`);
        const salas = await response.json();
        listaSalasElement.innerHTML = '';
        salas.forEach(sala => {
            const itemDaLista = document.createElement('li');
            itemDaLista.textContent = `${sala.nome} (Capacidade: ${sala.capacidade} pessoas)`;
            itemDaLista.addEventListener('click', () => selecionarSala(sala));
            listaSalasElement.appendChild(itemDaLista);
        });
    } catch (error) {
        mostrarMensagem('Falha ao carregar salas. Verifique se o backend está rodando.', 'erro');
    }
}

async function selecionarSala(sala) {
    salaSelecionadaGlobal = sala;
    salaSelecionadaTituloElement.textContent = `Agendamentos para: ${sala.nome}`;
    novoAgendamentoContainer.style.display = 'block';
    salaIdHiddenInput.value = sala.id;
    cancelarEdicao();

    try {
        const response = await fetch(`${API_URL}/salas/${sala.id}/agendamentos`);
        const agendamentosDaSala = await response.json();
        listaAgendamentosElement.innerHTML = '';
        if (agendamentosDaSala.length === 0) {
            listaAgendamentosElement.innerHTML = '<li>Nenhum agendamento para esta sala.</li>';
        } else {
            agendamentosDaSala.forEach(ag => {
                const itemDaLista = document.createElement('li');
                const textoAgendamento = document.createElement('span');
                const inicio = formatarDataHora(ag.data_inicio);
                const fim = formatarDataHora(ag.data_fim);
                textoAgendamento.textContent = `Responsável: ${ag.responsavel} | De: ${inicio} | Até: ${fim}`;
                
                const botaoDeletar = document.createElement('button');
                botaoDeletar.textContent = 'X';
                botaoDeletar.className = 'botao-deletar';
                botaoDeletar.addEventListener('click', () => deletarAgendamento(ag.id, sala));

                const botaoEditar = document.createElement('button');
                botaoEditar.textContent = 'Editar';
                botaoEditar.addEventListener('click', () => prepararEdicao(ag));

                itemDaLista.appendChild(textoAgendamento);
                itemDaLista.appendChild(botaoEditar);
                itemDaLista.appendChild(botaoDeletar);
                listaAgendamentosElement.appendChild(itemDaLista);
            });
        }
    } catch (error) {
        mostrarMensagem('Erro ao carregar agendamentos.', 'erro');
    }
}

function prepararEdicao(agendamento) {
    agendamentoEmEdicaoId = agendamento.id;
    const dataInicioFormatada = agendamento.data_inicio.slice(0, 16);
    const dataFimFormatada = agendamento.data_fim.slice(0, 16);
    responsavelInput.value = agendamento.responsavel;
    dataInicioInput.value = dataInicioFormatada;
    dataFimInput.value = dataFimFormatada;
    botaoSubmit.textContent = 'Salvar Alterações';
    botaoCancelarEdicao.style.display = 'block';
}

function cancelarEdicao() {
    agendamentoEmEdicaoId = null;
    formAgendamento.reset();
    botaoSubmit.textContent = 'Agendar';
    botaoCancelarEdicao.style.display = 'none';
}

async function deletarAgendamento(agendamentoId, salaAtual) {
    try {
        const response = await fetch(`${API_URL}/agendamentos/${agendamentoId}`, { method: 'DELETE' });
        if (response.ok) {
            selecionarSala(salaAtual);
        } else {
            mostrarMensagem('Falha ao deletar agendamento.', 'erro');
        }
    } catch (error) {
        mostrarMensagem('Erro de conexão ao deletar.', 'erro');
    }
}

formAgendamento.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dadosAgendamento = {
        sala_id: parseInt(salaIdHiddenInput.value),
        responsavel: responsavelInput.value,
        data_inicio: dataInicioInput.value,
        data_fim: dataFimInput.value,
    };
    let url = `${API_URL}/agendamentos`;
    let method = 'POST';
    if (agendamentoEmEdicaoId) {
        url = `${API_URL}/agendamentos/${agendamentoEmEdicaoId}`;
        method = 'PUT';
    }
    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dadosAgendamento),
        });
        const data = await response.json();
        if (response.ok) {
            const mensagem = agendamentoEmEdicaoId ? 'Agendamento atualizado com sucesso!' : 'Agendamento criado com sucesso!';
            mostrarMensagem(mensagem, 'sucesso');
            cancelarEdicao();
            selecionarSala(salaSelecionadaGlobal);
        } else {
            mostrarMensagem(data.mensagem, 'erro');
        }
    } catch (error) {
        mostrarMensagem('Erro de conexão. Tente novamente.', 'erro');
    }
});

botaoCancelarEdicao.addEventListener('click', cancelarEdicao);

carregarSalas();
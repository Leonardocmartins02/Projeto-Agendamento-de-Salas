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
const buscaSalasInput = document.getElementById('busca-salas');
const toastRegion = document.getElementById('toast-region');

// --- Variáveis de Estado ---
let salaSelecionadaGlobal = null;
let agendamentoEmEdicaoId = null;
let salasCache = [];

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
    // Painel legado (compatibilidade)
    if (painelMensagens) {
        painelMensagens.textContent = mensagem;
        painelMensagens.className = tipo === 'sucesso' ? 'mensagem-sucesso' : 'mensagem-erro';
        setTimeout(() => { painelMensagens.className = ''; }, 4000);
    }

    // Toasts modernos
    if (toastRegion) {
        const toast = document.createElement('div');
        toast.className = `toast ${tipo === 'sucesso' ? 'toast--success' : 'toast--error'}`;
        toast.setAttribute('role', 'status');
        toast.textContent = mensagem;
        toastRegion.appendChild(toast);
        setTimeout(() => { toast.remove(); }, 4000);
    }
}

function renderSalas(filtro = '') {
    if (!Array.isArray(salasCache)) return;
    const termo = filtro.trim().toLowerCase();
    listaSalasElement.innerHTML = '';

    const salasFiltradas = salasCache.filter(s => !termo || s.nome.toLowerCase().includes(termo));

    if (salasFiltradas.length === 0) {
        const vazio = document.createElement('li');
        vazio.textContent = termo ? 'Nenhuma sala encontrada.' : 'Sem salas disponíveis.';
        listaSalasElement.appendChild(vazio);
        return;
    }

    salasFiltradas.forEach(sala => {
        const itemDaLista = document.createElement('li');
        itemDaLista.className = 'list__item';
        itemDaLista.dataset.id = String(sala.id);
        itemDaLista.tabIndex = 0;
        itemDaLista.setAttribute('aria-selected', salaSelecionadaGlobal && salaSelecionadaGlobal.id === sala.id ? 'true' : 'false');

        const capacidade = document.createElement('span');
        capacidade.className = 'badge';
        capacidade.textContent = `Capacidade: ${sala.capacidade}`;

        const nome = document.createElement('span');
        nome.textContent = sala.nome + ' ';

        itemDaLista.appendChild(nome);
        itemDaLista.appendChild(capacidade);

        itemDaLista.addEventListener('click', () => selecionarSala(sala));
        itemDaLista.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selecionarSala(sala);
            }
        });

        // Destaque se já selecionada
        if (salaSelecionadaGlobal && salaSelecionadaGlobal.id === sala.id) {
            itemDaLista.classList.add('is-selected');
        }

        listaSalasElement.appendChild(itemDaLista);
    });
}

async function carregarSalas() {
    try {
        const response = await fetch(`${API_URL}/salas`);
        salasCache = await response.json();
        renderSalas(buscaSalasInput ? buscaSalasInput.value : '');
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

    // Atualiza destaque na lista de salas
    if (listaSalasElement) {
        [...listaSalasElement.children].forEach(li => {
            if (!(li instanceof HTMLElement)) return;
            const isAtiva = li.dataset && Number(li.dataset.id) === sala.id;
            li.classList.toggle('is-selected', Boolean(isAtiva));
            if (isAtiva) {
                li.setAttribute('aria-selected', 'true');
            } else {
                li.setAttribute('aria-selected', 'false');
            }
        });
    }

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
                botaoDeletar.textContent = 'Excluir';
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
        const confirmar = window.confirm('Tem certeza que deseja excluir este agendamento?');
        if (!confirmar) return;
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
/* Formulário de agendamento.
   Sempre que data, serviço, profissional ou cliente mudam, consulta /agendamentos/disponibilidade e:
   - refaz a lista de horários (de 10 em 10 min), bloqueando os indisponíveis e mostrando o motivo;
   - mostra no painel a ocupação do profissional no dia e quantos horários estão livres;
   - avisa na hora se o horário escolhido deixou de estar disponível.
   Assim o usuário vê a indisponibilidade antes de salvar (sugestões de Bruno e Vitória; defeito D7). */
(function () {
  "use strict";
  const form = document.getElementById("form-agendamento");
  if (!form) return;

  const cliente = document.getElementById("cliente_id");
  const servico = document.getElementById("servico_id");
  const profissional = document.getElementById("profissional_id");
  const data = document.getElementById("data");
  const hora = document.getElementById("hora");
  const previsao = document.getElementById("previsao-termino");
  const painel = document.getElementById("painel-disponibilidade");

  function nomeSelecionado(select) {
    const opcao = select.options[select.selectedIndex];
    return opcao && opcao.value ? opcao.text.split("·")[0].trim() : "";
  }

  function somarMinutos(hhmm, minutos) {
    const partes = hhmm.split(":").map(Number);
    const total = partes[0] * 60 + partes[1] + minutos;
    const h = Math.floor(total / 60), m = total % 60;
    return (h < 10 ? "0" : "") + h + ":" + (m < 10 ? "0" : "") + m;
  }

  function atualizarPrevisao() {
    const opcaoServico = servico.options[servico.selectedIndex];
    const duracao = opcaoServico ? Number(opcaoServico.dataset.duracao) : 0;
    if (duracao && hora.value) {
      previsao.textContent = "Término previsto: " + somarMinutos(hora.value, duracao) + " (" + duracao + " min)";
    } else if (!duracao && hora.value) {
      previsao.textContent = "Escolha o serviço para ver o horário de término.";
    } else {
      previsao.textContent = "";
    }
  }

  function preencherHorarios(horarios, fechado) {
    const escolhido = hora.value;
    hora.innerHTML = "";
    const livres = horarios.filter(function (h) { return h.livre; }).length;
    const primeira = new Option(fechado ? "Fechado neste dia" : (livres ? "Selecione…" : "Nenhum horário livre neste dia"), "");
    hora.appendChild(primeira);
    let aindaDisponivel = false;
    horarios.forEach(function (h) {
      const opcao = new Option(h.livre ? h.hora : h.hora + " · indisponível: " + h.motivo, h.hora);
      opcao.disabled = !h.livre;
      if (h.hora === escolhido && h.livre) { opcao.selected = true; aindaDisponivel = true; }
      hora.appendChild(opcao);
    });
    return { livres: livres, perdeuEscolha: Boolean(escolhido) && !aindaDisponivel, escolhido: escolhido };
  }

  function mostrarPainel(info, resumo) {
    painel.innerHTML = "";
    painel.hidden = false;
    const titulo = document.createElement("strong");
    painel.appendChild(titulo);

    if (info.fechado) {
      titulo.textContent = "O estabelecimento não abre neste dia. Escolha outra data.";
      painel.className = "disponibilidade disponibilidade-alerta";
      return;
    }
    if (resumo.perdeuEscolha) {
      const aviso = document.createElement("p");
      aviso.className = "aviso-horario";
      aviso.textContent = "O horário " + resumo.escolhido + " não está mais disponível com estas escolhas. Selecione outro.";
      painel.insertBefore(aviso, titulo);  // o aviso vem primeiro: é o que exige ação
    }
    painel.className = "disponibilidade" + (resumo.livres ? "" : " disponibilidade-alerta");
    const nome = nomeSelecionado(profissional);
    if (!resumo.livres && !info.ocupados.length) {
      titulo.textContent = "Não há mais horários disponíveis nesta data. Escolha outra data.";
      return;
    }
    if (!nome) {
      titulo.textContent = resumo.livres + " horários possíveis neste dia. Escolha o profissional para ver a agenda dele.";
      return;
    }
    if (!info.ocupados.length) {
      titulo.textContent = nome + " está livre o dia todo (" + info.abertura + " às " + info.fechamento + "): " +
        resumo.livres + " horários disponíveis.";
      return;
    }
    titulo.textContent = resumo.livres
      ? nome + " tem " + resumo.livres + " horários livres. Já ocupados:"
      : "Nenhum horário livre para " + nome + " neste dia. Ocupados:";
    const lista = document.createElement("ul");
    info.ocupados.forEach(function (o) {
      const item = document.createElement("li");
      item.textContent = o.inicio + "–" + o.fim + " · " + o.servico;
      lista.appendChild(item);
    });
    painel.appendChild(lista);
  }

  let controlador = null;
  function atualizarDisponibilidade() {
    if (!data.value) { painel.hidden = true; return; }
    if (controlador) controlador.abort();
    controlador = new AbortController();
    const params = new URLSearchParams({ data: data.value });
    if (profissional.value) params.set("profissional_id", profissional.value);
    if (servico.value) params.set("servico_id", servico.value);
    if (cliente.value) params.set("cliente_id", cliente.value);
    if (form.dataset.ignorar) params.set("ignorar", form.dataset.ignorar);
    painel.hidden = false;
    painel.className = "disponibilidade";
    painel.textContent = "Consultando horários…";
    fetch(form.dataset.urlDisponibilidade + "?" + params, { signal: controlador.signal, headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (info) {
        const resumo = preencherHorarios(info.horarios, info.fechado);
        mostrarPainel(info, resumo);
        atualizarPrevisao();
      })
      .catch(function (erro) {
        if (erro.name === "AbortError") return;
        painel.textContent = "Não foi possível consultar a agenda agora. Você ainda pode salvar: o sistema verifica conflitos.";
      });
  }

  [cliente, servico, profissional, data].forEach(function (campo) {
    campo.addEventListener("change", atualizarDisponibilidade);
  });
  hora.addEventListener("change", atualizarPrevisao);
  atualizarPrevisao();
  atualizarDisponibilidade();
})();

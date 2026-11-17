/* Formulário de agendamento: mostra o horário de término e os horários já ocupados
   do profissional no dia escolhido (consulta /agendamentos/disponibilidade). */
(function () {
  "use strict";
  const form = document.getElementById("form-agendamento");
  if (!form) return;

  const servico = document.getElementById("servico_id");
  const profissional = document.getElementById("profissional_id");
  const data = document.getElementById("data");
  const hora = document.getElementById("hora");
  const previsao = document.getElementById("previsao-termino");
  const painel = document.getElementById("painel-disponibilidade");

  function somarMinutos(hhmm, minutos) {
    const partes = hhmm.split(":").map(Number);
    const total = partes[0] * 60 + partes[1] + minutos;
    const h = Math.floor(total / 60), m = total % 60;
    return (h < 10 ? "0" : "") + h + ":" + (m < 10 ? "0" : "") + m;
  }

  function atualizarPrevisao() {
    const opcao = servico.options[servico.selectedIndex];
    const duracao = opcao ? Number(opcao.dataset.duracao) : 0;
    if (duracao && hora.value) {
      previsao.textContent = "Término previsto: " + somarMinutos(hora.value, duracao) + " (" + duracao + " min)";
    } else {
      previsao.textContent = "";
    }
  }

  let controlador = null;
  function atualizarDisponibilidade() {
    if (!profissional.value || !data.value) { painel.hidden = true; return; }
    if (controlador) controlador.abort();
    controlador = new AbortController();
    const params = new URLSearchParams({ profissional_id: profissional.value, data: data.value });
    if (form.dataset.ignorar) params.set("ignorar", form.dataset.ignorar);
    painel.hidden = false;
    painel.textContent = "Consultando agenda…";
    fetch(form.dataset.urlDisponibilidade + "?" + params, { signal: controlador.signal, headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (info) {
        painel.innerHTML = "";
        const titulo = document.createElement("strong");
        const nome = profissional.options[profissional.selectedIndex].text.split("·")[0].trim();
        if (info.fechado) {
          titulo.textContent = "O estabelecimento não abre neste dia.";
          painel.appendChild(titulo);
          return;
        }
        if (!info.ocupados.length) {
          titulo.textContent = nome + " está livre o dia todo (" + info.abertura + " às " + info.fechamento + ").";
          painel.appendChild(titulo);
          return;
        }
        titulo.textContent = "Horários já ocupados de " + nome + ":";
        painel.appendChild(titulo);
        const lista = document.createElement("ul");
        info.ocupados.forEach(function (o) {
          const item = document.createElement("li");
          item.textContent = o.inicio + "–" + o.fim + " · " + o.servico;
          lista.appendChild(item);
        });
        painel.appendChild(lista);
      })
      .catch(function (erro) {
        if (erro.name === "AbortError") return;
        painel.textContent = "Não foi possível consultar a agenda agora. Você ainda pode salvar; o sistema verifica conflitos.";
      });
  }

  servico.addEventListener("change", atualizarPrevisao);
  hora.addEventListener("input", atualizarPrevisao);
  profissional.addEventListener("change", atualizarDisponibilidade);
  data.addEventListener("change", atualizarDisponibilidade);
  atualizarPrevisao();
  atualizarDisponibilidade();
})();

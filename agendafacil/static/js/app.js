/* AgendaFácil: comportamentos comuns a todas as telas (JavaScript puro, sem bibliotecas). */
(function () {
  "use strict";

  // Menu no celular
  const botaoMenu = document.querySelector("[data-menu]");
  const menu = document.getElementById("menu");
  if (botaoMenu && menu) {
    botaoMenu.addEventListener("click", function () {
      const aberto = menu.classList.toggle("aberto");
      botaoMenu.setAttribute("aria-expanded", String(aberto));
    });
  }

  // Fechar alertas. Eles não somem sozinhos: sumir de repente desloca a página
  // enquanto a pessoa vai clicar em algo (defeito D2 do laudo de qualidade).
  document.querySelectorAll("[data-fechar-alerta]").forEach(function (botao) {
    botao.addEventListener("click", function () { botao.closest(".alerta").remove(); });
  });

  // Máscara de telefone: (11) 98765-4321
  function mascararTelefone(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length <= 2) return d.length ? "(" + d : "";
    if (d.length <= 6) return "(" + d.slice(0, 2) + ") " + d.slice(2);
    if (d.length <= 10) return "(" + d.slice(0, 2) + ") " + d.slice(2, 6) + "-" + d.slice(6);
    return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
  }
  document.querySelectorAll('[data-mascara="telefone"]').forEach(function (campo) {
    campo.value = mascararTelefone(campo.value);
    campo.addEventListener("input", function () { campo.value = mascararTelefone(campo.value); });
  });

  // Confirmação antes de ações destrutivas (excluir, cancelar)
  const dialogo = document.getElementById("dialogo-confirmar");
  document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      if (form.dataset.confirmado === "1") return;
      evento.preventDefault();
      const texto = form.dataset.confirmar;
      if (!dialogo || typeof dialogo.showModal !== "function") {
        if (window.confirm(texto)) { form.dataset.confirmado = "1"; form.submit(); }
        return;
      }
      document.getElementById("dialogo-texto").textContent = texto;
      dialogo.returnValue = "";
      dialogo.showModal();
      dialogo.addEventListener("close", function aoFechar() {
        dialogo.removeEventListener("close", aoFechar);
        if (dialogo.returnValue === "confirmar") { form.dataset.confirmado = "1"; form.submit(); }
      });
    });
  });

  // Validação no navegador com mensagens em português, ao lado do campo.
  // O servidor valida de novo: esta etapa é só para dar retorno imediato.
  function mensagemPara(campo) {
    const v = campo.validity;
    if (v.valueMissing) return "Campo obrigatório.";
    if (v.typeMismatch && campo.type === "email") return "Digite um e-mail válido, ex.: nome@dominio.com.";
    if (v.tooShort) return "Use pelo menos " + campo.minLength + " caracteres.";
    if (v.tooLong) return "Use no máximo " + campo.maxLength + " caracteres.";
    if (v.rangeUnderflow) return "O valor mínimo é " + campo.min + ".";
    if (v.rangeOverflow) return "O valor máximo é " + campo.max + ".";
    if (v.patternMismatch) return campo.dataset.mascara === "telefone"
      ? "Telefone com DDD, ex.: (11) 98765-4321." : "Formato inválido.";
    if (v.customError) return campo.validationMessage;
    if (!v.valid) return "Valor inválido.";
    return "";
  }

  function validarCampo(campo) {
    if (campo.dataset.igualA) {
      const outro = document.getElementById(campo.dataset.igualA);
      campo.setCustomValidity(outro && outro.value !== campo.value ? "As senhas não conferem." : "");
    }
    if (campo.type === "file" && campo.dataset.maxBytes && campo.files && campo.files[0]) {
      campo.setCustomValidity(campo.files[0].size > Number(campo.dataset.maxBytes) ? "A imagem deve ter no máximo 2 MB." : "");
    }
    const recipiente = campo.closest(".campo") || campo.parentElement;
    let erro = recipiente.querySelector(".erro-campo");
    const mensagem = mensagemPara(campo);
    if (mensagem) {
      if (!erro) {
        erro = document.createElement("span");
        erro.className = "erro-campo";
        erro.id = (campo.id || campo.name) + "-erro";
        recipiente.appendChild(erro);
      }
      erro.textContent = mensagem;
      recipiente.classList.add("campo-invalido");
      campo.setAttribute("aria-invalid", "true");
    } else if (erro) {
      erro.remove();
      recipiente.classList.remove("campo-invalido");
      campo.removeAttribute("aria-invalid");
    }
    return !mensagem;
  }

  document.querySelectorAll("form[data-validar]").forEach(function (form) {
    const campos = form.querySelectorAll("input, select, textarea");
    // Os erros aparecem no envio e somem enquanto a pessoa corrige o campo.
    // Não validamos no "blur": inserir ou remover a mensagem nesse momento desloca a página
    // e o clique que tirou o foco (ex.: no link "Crie uma agora" ou no botão Salvar) cai em
    // outro lugar (defeito D1 do laudo de qualidade).
    function revalidarSeComErro(campo) {
      if (campo.getAttribute("aria-invalid") === "true") validarCampo(campo);
    }
    campos.forEach(function (campo) {
      campo.addEventListener("input", function () {
        revalidarSeComErro(campo);
        form.querySelectorAll('[data-igual-a="' + campo.id + '"]').forEach(revalidarSeComErro);
      });
      campo.addEventListener("change", function () { revalidarSeComErro(campo); });
    });
    form.addEventListener("submit", function (evento) {
      let primeiroInvalido = null;
      campos.forEach(function (campo) {
        if (campo.type === "hidden") return;
        if (!validarCampo(campo) && !primeiroInvalido) primeiroInvalido = campo;
      });
      if (primeiroInvalido) {
        evento.preventDefault();
        primeiroInvalido.focus();
        return;
      }
      // Evita envio duplicado (duplo clique)
      form.querySelectorAll('button[type="submit"]').forEach(function (b) {
        setTimeout(function () { b.disabled = true; }, 0);
      });
    });
  });
})();

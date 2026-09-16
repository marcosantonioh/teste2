function fecharModal() {
  const modal = document.getElementById("modalSemVidas");
  if (modal) {
    const url = modal.getAttribute("data-redirect");
    window.location.href = url;
  }
}

function fecharModalSair() {
  const modal = document.getElementById("modalSair");
  if (modal) {
    modal.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector(".form-layout-container");
  const containerExercicio = document.querySelector(".container-exercicio");
  const pathPercurso = form.dataset.percursoUrl || "/exercicios/percurso/";
  const semVidasInicial =
    form.dataset.semVidas === "True" || form.dataset.semVidas === "true";
  const mascoteVerde = "/static/img/mascote/verde.svg";
  const mascoteVermelho = "/static/img/mascote/vermelho.svg";
  const modalConquista = document.getElementById("modalConquista");
  const listaConquistas = document.getElementById("conquistasNovas");
  const modalOfensivaGanha = document.getElementById("modalOfensivaGanha");
  const totalOfensivaGanha = document.getElementById("totalOfensivaGanha");
  const diasOfensivaGanha = document.getElementById("diasOfensivaGanha");
  let aoFecharModalConquista = null;
  let aoFecharModalOfensiva = null;

  function fecharModalConquista() {
    if (!modalConquista) return;
    modalConquista.classList.remove("modal-conquista--aberto");
    modalConquista.setAttribute("aria-hidden", "true");
    const acao = aoFecharModalConquista;
    aoFecharModalConquista = null;
    if (acao) acao();
  }

  function mostrarModalConquistas(conquistas, aoFechar = null) {
    if (!modalConquista || !listaConquistas || !conquistas?.length) {
      if (aoFechar) aoFechar();
      return;
    }
    listaConquistas.replaceChildren();
    conquistas.forEach((conquista) => {
      const item = document.createElement("article");
      item.className = "modal-conquista__item";
      if (conquista.avatar_url) {
        const avatar = document.createElement("img");
        avatar.className = "modal-conquista__avatar";
        avatar.src = conquista.avatar_url;
        avatar.alt = `Avatar ${conquista.avatar_nome || "desbloqueado"}`;
        item.append(avatar);
      }
      const texto = document.createElement("div");
      const nome = document.createElement("strong");
      nome.textContent = conquista.nome;
      const descricao = document.createElement("p");
      descricao.textContent = conquista.avatar_nome
        ? `${conquista.descricao} Avatar ${conquista.avatar_nome} desbloqueado!`
        : conquista.descricao;
      texto.append(nome, descricao);
      item.append(texto);
      listaConquistas.append(item);
    });
    aoFecharModalConquista = aoFechar;
    modalConquista.classList.add("modal-conquista--aberto");
    modalConquista.setAttribute("aria-hidden", "false");
    modalConquista.querySelector("[data-fechar-conquista]")?.focus();
  }

  function mostrarModalOfensiva(foiObtida, total, diasSemana, aoFechar) {
    if (!foiObtida || !modalOfensivaGanha || !totalOfensivaGanha || !diasOfensivaGanha) {
      aoFechar();
      return;
    }
    totalOfensivaGanha.textContent = total;
    diasOfensivaGanha.replaceChildren();
    diasSemana.forEach((dia) => {
      const item = document.createElement("div");
      item.className = "modal-ofensiva-ganha__dia";
      const circulo = document.createElement("span");
      circulo.className = "modal-ofensiva-ganha__circulo";
      if (dia.concluido) {
        circulo.classList.add("modal-ofensiva-ganha__circulo--concluido");
        const check = document.createElement("img");
        check.src = "/static/img/check-white.svg";
        check.alt = "Dia concluído";
        circulo.append(check);
      }
      const inicial = document.createElement("span");
      inicial.textContent = dia.inicial;
      item.append(circulo, inicial);
      diasOfensivaGanha.append(item);
    });
    aoFecharModalOfensiva = aoFechar;
    modalOfensivaGanha.classList.add("modal-ofensiva-ganha--aberto");
    modalOfensivaGanha.setAttribute("aria-hidden", "false");
    modalOfensivaGanha.querySelector("[data-fechar-ofensiva-ganha]")?.focus();
  }

  function fecharModalOfensiva() {
    if (!modalOfensivaGanha) return;
    modalOfensivaGanha.classList.remove("modal-ofensiva-ganha--aberto");
    modalOfensivaGanha.setAttribute("aria-hidden", "true");
    const acao = aoFecharModalOfensiva;
    aoFecharModalOfensiva = null;
    if (acao) acao();
  }

  // --- ALTERAÇÃO 1: Capturamos o HTML inicial dos botões ---
  const htmlBotoesPadrao = document.querySelector(
    ".base-acoes-exercicio",
  ).innerHTML;

  // Função genérica para enviar dados via AJAX
  async function enviarAcaoAjax(acao) {
    syncLacunaHiddenInput();
    const formData = new FormData(form);

    if (acao === "responder") {
      if (form.dataset.respostaEnviada === "true") return;
      form.dataset.respostaEnviada = "true";
      disableInputs();
    }

    const url = form.action;

    formData.append("acao", acao); // 'responder' ou 'pular'
    formData.append("is_ajax_request", "1");

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(
          `O servidor retornou um erro para a ação "${acao}":`,
          errorText,
        );
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Se a ação for 'pular', a view vai redirecionar, então o 'fetch' pega isso.
      // Se o redirect acontecer, a página vai para o próximo exercício.
      if (response.redirected) {
        window.location.href = response.url;
        return;
      }

      const data = await response.json();
      processApiResponse(data);
    } catch (error) {
      if (acao === "responder") {
        delete form.dataset.respostaEnviada;
        form.querySelectorAll('input[type="radio"]').forEach((input) => {
          input.disabled = false;
        });
        updateResponderButtonState();
      }
      console.error(`Erro completo na ação "${acao}":`, error);
      alert(
        "Ocorreu um erro de comunicação com o servidor. Verifique o console.",
      );
    }
  }

  async function loadNextExercise(nextId) {
    if (!nextId || nextId === "null") {
      window.location.href = pathPercurso;
      return;
    }
    const url = `/exercicios/api/exercicio/${nextId}/`;

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Falha ao buscar o próximo exercício.");
      const exercicioData = await response.json();
      renderNewExercise(exercicioData);
    } catch (error) {
      console.error("Erro ao carregar próximo exercício:", error);
      window.location.href = `/exercicios/resolver/${nextId}/`;
    }
  }

  function processApiResponse(data) {
    const exibirResultado = () => {
      const concluir = () => {
        if (data.estacao_concluida_url) {
          window.location.href = data.estacao_concluida_url;
          return;
        }
        if (data.sem_vidas) {
          const modalSemVidas = document.getElementById("modalSemVidas");
          if (modalSemVidas) modalSemVidas.style.display = "flex";
          return;
        }
        updateProgressBar(data.progresso);
        renderFeedback(data);
      };

      mostrarModalOfensiva(
        data.ofensiva_obtida,
        data.ofensiva_atual,
        data.ofensiva_dias_semana,
        concluir,
      );
    };
    mostrarModalConquistas(data.conquistas_novas, exibirResultado);
  }

  function renderFeedback(data) {
    const baseAcoes = document.querySelector(".base-acoes-exercicio");
    if (!baseAcoes) return;
    baseAcoes.innerHTML = "";
    const mascoteSrc =
      data.resultado === "correto" ? mascoteVerde : mascoteVermelho;
    const feedbackClass = data.resultado;
    const feedbackText =
      data.resultado === "correto"
        ? "Resposta Correta!"
        : "Resposta Incorreta!";
    let actionButtonsHtml = "";
    if (data.resultado === "correto") {
      actionButtonsHtml = `<button type="button" class="botao-reportar" data-abrir-report>⚑ Reportar problema</button><a href="#" data-next-id="${data.proximo_exercicio_id}" class="submit btn-continuar-ajax">Continuar</a>`;
    } else {
      actionButtonsHtml = `<div class="botoes-incorreto"><button type="button" onclick="window.location.reload();" class="btn-tentar-novamente">Tentar Novamente</button><button type="button" class="botao-reportar" data-abrir-report>⚑ Reportar problema</button><a href="#" data-next-id="${data.proximo_exercicio_id}" class="btn-continuar btn-continuar-ajax">Pular Exercício</a></div>`;
    }
    const feedbackHtml = `<img src="${mascoteSrc}" alt="Mascote Feedback" class="mascote-feedback" /><div class="resultado ${feedbackClass}"><p>${feedbackText}</p>${actionButtonsHtml}</div>`;
    baseAcoes.insertAdjacentHTML("beforeend", feedbackHtml);
    highlightAnswers(data);
    disableInputs();
  }

  function getDefaultActionButtonsHtml() {
    return `<div class="container-botoes"><button type="button" id="botao-pular-exercicio" class="pular">Pular</button><button type="button" id="botao-responder-exercicio" class="submit" disabled>Responder</button></div>`;
  }

  function renderNewExercise(data) {
    history.pushState(null, "", data.url_resolucao);
    form.action = data.url_resolucao;
    const formReport = document.getElementById("formReport");
    if (formReport) formReport.action = `${data.url_resolucao}reportar/`;
    delete form.dataset.respostaEnviada;
    const conteudoWrapper = document.querySelector(
      ".conteudo-exercicio-wrapper",
    );
    const baseAcoes = document.querySelector(".base-acoes-exercicio");
    let newExerciseHtml = "";
    if (data.tipo === "mcq") {
      let alternativasHtml = data.alternativas
        .map(
          ([numero, texto], index) =>
            `<input type="radio" name="resposta" id="alt${numero}" value="${numero}" hidden class="alternativa-exercicio" /><label for="alt${numero}" class="botao-alternativa"><span class="numero-alternativa">${index + 1}</span><span class="texto-alternativa">${texto}</span></label>`,
        )
        .join("");
      newExerciseHtml = `<div class="formulario"><div class="exercicio-mcq-layout"><div class="exercicio-mcq-conteudo">${
        data.enunciado
          ? `<p class="exercicio-enunciado">${data.enunciado}</p>`
          : ""
      }${
        data.codigo ? `<pre class="exercicio-codigo">${data.codigo}</pre>` : ""
      }</div><div class="exercicio-mcq-alternativas"><div class="alternativas"><h3>Alternativas</h3>${alternativasHtml}</div></div></div></div>`;
    } else if (data.tipo === "lacuna") {
      newExerciseHtml = `<div class="formulario"><div class="exercicio-lacuna-layout">${
        data.enunciado
          ? `<p class="exercicio-enunciado">${data.enunciado}</p>`
          : ""
      }${
        data.codigo_renderizado
          ? `<pre class="exercicio-codigo">${data.codigo_renderizado}</pre>`
          : ""
      }${
        data.codigo_renderizado
          ? `<p class="lacuna-hint">Clique no campo destacado e digite a resposta.</p>`
          : ""
      }</div></div>`;
    } else if (data.tipo === "vf") {
      newExerciseHtml = `<div class="formulario"><div class="exercicio-vf-layout"><div class="exercicio-vf-conteudo">${
        data.enunciado
          ? `<p class="exercicio-enunciado">${data.enunciado}</p>`
          : ""
      }<div class="exercicio-vf-alternativas"><div class="alternativas-vf">${`<input type="radio" name="resposta_vf" id="vf_true" value="True" class="alternativa-exercicio-vf" hidden /><label for="vf_true" class="botao-alternativa">Verdadeiro</label><input type="radio" name="resposta_vf" id="vf_false" value="False" class="alternativa-exercicio-vf" hidden /><label for="vf_false" class="botao-alternativa">Falso</label>`}</div></div></div></div>`;
    } else if (data.tipo === "info") {
      newExerciseHtml = `<div class="formulario"><div class="exercicio-info-layout">${
        data.enunciado
          ? `<p class="exercicio-enunciado">${data.enunciado}</p>`
          : ""
      }${
        data.codigo ? `<pre class="exercicio-codigo">${data.codigo}</pre>` : ""
      }${
        data.imagem_url
          ? `<img src="${data.imagem_url}" alt="Imagem do exercício" class="exercicio-imagem" />`
          : ""
      }</div></div>`;
    } else {
      newExerciseHtml = `<div class="formulario"><div class="exercicio-erro"><p>Tipo de exercício não suportado: ${data.tipo}</p></div></div>`;
    }
    conteudoWrapper.innerHTML = newExerciseHtml;

    if (data.tipo === "info") {
      baseAcoes.innerHTML = `<div class="resultado"><a href="#" data-next-id="${
        data.proximo_exercicio_id || "null"
      }" class="submit btn-continuar-ajax">Continuar</a></div>`;
    } else {
      baseAcoes.innerHTML = getDefaultActionButtonsHtml();
    }

    initializeEventListeners();
    mostrarModalConquistas(data.conquistas_novas);
  }

  function updateProgressBar(progressData) {
    const progressBar = document.querySelector(".barra-progresso-preenchida");
    const vidasContador = document.querySelector(".contador-vida");
    if (progressBar) progressBar.style.width = `${progressData.percentual}%`;
    if (vidasContador && progressData.vidas_atuais !== undefined)
      vidasContador.textContent = progressData.vidas_atuais;
  }

  function highlightAnswers(data) {
    document.querySelectorAll(".botao-alternativa").forEach((label) => {
      const input = document.getElementById(label.getAttribute("for"));
      if (!input) return;
      const alternativeValue = input.value;
      if (
        String(alternativeValue).toLowerCase() ==
        String(data.resposta_correta).toLowerCase()
      ) {
        label.classList.add("alternativa-correta");
      }
      if (
        !data.correta &&
        String(alternativeValue).toLowerCase() ==
          String(data.resposta_submetida).toLowerCase()
      ) {
        label.classList.add("alternativa-incorreta");
      }
    });
  }

  function disableInputs() {
    form.querySelectorAll('input[type="radio"]').forEach((input) => {
      input.disabled = true;
    });
    form.querySelectorAll('input[type="text"], textarea').forEach((input) => {
      input.disabled = true;
    });
  }

  function isTypingInTextField(event) {
    const target = event.target;
    if (!target) return false;
    const tag = target.tagName.toLowerCase();
    if (target.isContentEditable === true) return true;
    if (tag === "textarea") return true;
    if (tag !== "input") return false;

    const typingInputTypes = [
      "text",
      "search",
      "email",
      "tel",
      "url",
      "password",
      "number",
      "date",
      "datetime-local",
      "month",
      "week",
      "time",
      "textarea",
    ];
    return typingInputTypes.includes(target.type);
  }

  function syncLacunaHiddenInput() {
    const lacunaInput = form.querySelector('input.lacuna-marker[name="resposta"]');
    return lacunaInput ? lacunaInput.value.trim().length > 0 : false;
  }

  function selectAlternativeByKey(key) {
    const alternativasLabels = form.querySelectorAll(
      ".alternativas .botao-alternativa, .alternativas-vf .botao-alternativa",
    );
    for (const label of alternativasLabels) {
      const numeroElemento = label.querySelector(".numero-alternativa");
      if (!numeroElemento) continue;
      if (numeroElemento.textContent.trim() !== key) continue;

      const inputId = label.getAttribute("for");
      const alternativa = inputId ? document.getElementById(inputId) : null;
      if (!alternativa || alternativa.disabled) return false;

      alternativa.checked = true;
      const changeEvent = new Event("change", { bubbles: true });
      alternativa.dispatchEvent(changeEvent);

      label.focus();
      return true;
    }
    return false;
  }

  function handleEnterKey() {
    const botaoResponder = document.getElementById("botao-responder-exercicio");
    const botaoContinuarAjax = document.querySelector(
      ".btn-continuar-ajax:not([disabled])",
    );

    if (botaoResponder && !botaoResponder.disabled) {
      botaoResponder.click();
      return true;
    }

    if (botaoContinuarAjax) {
      botaoContinuarAjax.click();
      return true;
    }

    return false;
  }

  // DENTRO DO SEU SCRIPT PRINCIPAL

  function updateResponderButtonState() {
    const responderButton = document.getElementById(
      "botao-responder-exercicio",
    );

    if (!responderButton) return; // Se o botão não existir, a função para.

    const algumaAlternativaMarcada = form.querySelector(
      'input[type="radio"]:checked',
    );
    const textoLacuna = form.querySelector('input[type="text"], textarea');
    const lacunaInput = form.querySelector('input.lacuna-marker[name="resposta"]');
    const lacunaPreenchida = textoLacuna
      ? textoLacuna.value.trim().length > 0
      : lacunaInput
        ? lacunaInput.value.trim().length > 0
        : false;
    responderButton.disabled = !(algumaAlternativaMarcada || lacunaPreenchida);
  }

  function initializeEventListeners() {
    // PROCURA PELOS NOVOS BOTÕES PELO ID
    const botaoResponder = document.getElementById("botao-responder-exercicio");
    const botaoPular = document.getElementById("botao-pular-exercicio");

    // Adiciona o listener para o clique em "Responder"
    if (botaoResponder) {
      botaoResponder.addEventListener("click", () =>
        enviarAcaoAjax("responder"),
      );
    }

    // Adiciona o listener para o clique em "Pular"
    if (botaoPular) {
      botaoPular.addEventListener("click", () => {
        // Para "Pular", não precisamos de AJAX complexo, podemos só redirecionar
        // como a view já faz. A forma mais simples é submeter o formulário
        // da maneira antiga SÓ para esta ação.
        const form = document.querySelector(".form-layout-container");
        const pularInput = document.createElement("input");
        pularInput.type = "hidden";
        pularInput.name = "acao";
        pularInput.value = "pular";
        form.appendChild(pularInput);
        form.submit();
      });
    }

    const alternativasDiv = form.querySelector(
      ".alternativas, .alternativas-vf",
    );
    if (alternativasDiv)
      alternativasDiv.addEventListener("change", updateResponderButtonState);

    const textoLacuna = form.querySelector('input[type="text"], textarea');
    if (textoLacuna) {
      textoLacuna.addEventListener("input", updateResponderButtonState);
    }
    const lacunaInput = form.querySelector('input.lacuna-marker[name="resposta"]');
    if (lacunaInput) {
      lacunaInput.addEventListener("input", updateResponderButtonState);
    }

    updateResponderButtonState();
  }

  const botaoSair = document.getElementById("abrirModal");
  if (botaoSair) {
    botaoSair.addEventListener("click", (e) => {
      e.preventDefault();
      const modalSair = document.getElementById("modalSair");
      if (modalSair) modalSair.style.display = "flex";
    });
  }

  const modalReport = document.getElementById("modalReport");
  const fecharReport = document.querySelector("[data-fechar-report]");
  function abrirModalReport() {
    if (modalReport) {
      modalReport.classList.add("modal-report--aberto");
      modalReport.setAttribute("aria-hidden", "false");
      document.getElementById("motivoReport")?.focus();
    }
  }
  if (fecharReport && modalReport) {
    fecharReport.addEventListener("click", () => {
      modalReport.classList.remove("modal-report--aberto");
      modalReport.setAttribute("aria-hidden", "true");
    });
  }
  if (modalReport) {
    modalReport.addEventListener("click", (event) => {
      if (event.target === modalReport) fecharReport?.click();
    });
  }

  modalConquista?.querySelectorAll("[data-fechar-conquista]").forEach((botao) => {
    botao.addEventListener("click", fecharModalConquista);
  });
  modalOfensivaGanha?.querySelector("[data-fechar-ofensiva-ganha]")?.addEventListener(
    "click",
    fecharModalOfensiva,
  );
  modalConquista?.addEventListener("click", (event) => {
    if (event.target === modalConquista) fecharModalConquista();
  });

  document.addEventListener("keydown", (event) => {
    if (isTypingInTextField(event)) return;

    if (event.key === "Enter") {
      const handled = handleEnterKey();
      if (handled) {
        event.preventDefault();
      }
      return;
    }

    const key = event.key;
    if (!/^[1-4]$/.test(key)) return;

    const selecionou = selectAlternativeByKey(key);
    if (selecionou) {
      event.preventDefault();
      updateResponderButtonState();
    }
  });

  if (semVidasInicial) {
    const modalSemVidas = document.getElementById("modalSemVidas");
    if (modalSemVidas) modalSemVidas.style.display = "flex";
  }

  containerExercicio.addEventListener("click", function (event) {
    const reportButton = event.target.closest("[data-abrir-report]");
    if (reportButton) {
      abrirModalReport();
      return;
    }
    const target = event.target.closest(".btn-continuar-ajax");
    if (target) {
      event.preventDefault();
      loadNextExercise(target.dataset.nextId);
    }
  });

  initializeEventListeners();
  const conquistasIniciais = JSON.parse(
    document.getElementById("conquistasIniciais")?.textContent || "[]",
  );
  mostrarModalConquistas(conquistasIniciais);
});

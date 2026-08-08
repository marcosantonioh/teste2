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
      actionButtonsHtml = `<a href="#" data-next-id="${data.proximo_exercicio_id}" class="submit btn-continuar-ajax">Continuar</a>`;
    } else {
      actionButtonsHtml = `<div class="botoes-incorreto"><button type="button" onclick="window.location.reload();" class="btn-tentar-novamente">Tentar Novamente</button><a href="#" data-next-id="${data.proximo_exercicio_id}" class="btn-continuar btn-continuar-ajax">Pular Exercício</a></div>`;
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
          ? `<p class="lacuna-hint">Clique no espaço sublinhado e digite a resposta.</p>`
          : ""
      }<input type="hidden" id="resposta" name="resposta" value="" /></div></div>`;
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
  }

  function updateProgressBar(progressData) {
    const progressBar = document.querySelector(
      ".barra-progresso-preenchimento",
    );
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
    const lacunaSpan = form.querySelector(
      '.lacuna-marker[contenteditable="true"]',
    );
    const respostaInput = form.querySelector(
      'input[type="hidden"][name="resposta"]',
    );
    if (lacunaSpan && respostaInput) {
      const texto = lacunaSpan.textContent.trim();
      respostaInput.value = texto === "______" ? "" : texto;
      return respostaInput.value.trim().length > 0;
    }
    return false;
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
    const lacunaSpan = form.querySelector(
      '.lacuna-marker[contenteditable="true"]',
    );
    const lacunaPreenchida = textoLacuna
      ? textoLacuna.value.trim().length > 0
      : lacunaSpan
        ? lacunaSpan.textContent.trim().length > 0
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
    const lacunaSpan = form.querySelector(
      '.lacuna-marker[contenteditable="true"]',
    );
    if (lacunaSpan) {
      lacunaSpan.addEventListener("input", () => {
        syncLacunaHiddenInput();
        updateResponderButtonState();
      });
      lacunaSpan.addEventListener("focus", () => {
        if (lacunaSpan.textContent.trim() === "______") {
          lacunaSpan.textContent = "";
        }
      });
      lacunaSpan.addEventListener("blur", () => {
        if (lacunaSpan.textContent.trim().length === 0) {
          lacunaSpan.textContent = "______";
        }
      });
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
    const target = event.target.closest(".btn-continuar-ajax");
    if (target) {
      event.preventDefault();
      loadNextExercise(target.dataset.nextId);
    }
  });

  initializeEventListeners();
});

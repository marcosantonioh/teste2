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

  // --- ALTERAÇÃO 1: Capturamos o HTML inicial dos botões ---
  const htmlBotoesPadrao = document.querySelector(
    ".base-acoes-exercicio"
  ).innerHTML;

  // Função genérica para enviar dados via AJAX
  async function enviarAcaoAjax(acao) {
    const formData = new FormData(form);
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
          errorText
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
      console.error(`Erro completo na ação "${acao}":`, error);
      alert(
        "Ocorreu um erro de comunicação com o servidor. Verifique o console."
      );
    }
  }

  async function loadNextExercise(nextId) {
    if (!nextId || nextId === "null") {
      window.location.href =
        "{% url 'exercicios:percurso' exercicio.modulo.id %}";
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
      data.resultado === "correto"
        ? "{% static 'img/mascote/verde.svg' %}"
        : "{% static 'img/mascote/vermelho.svg' %}";
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

  function renderNewExercise(data) {
    history.pushState(null, "", data.url_resolucao);
    form.action = data.url_resolucao;
    const conteudoWrapper = document.querySelector(
      ".conteudo-exercicio-wrapper"
    );
    const baseAcoes = document.querySelector(".base-acoes-exercicio");
    let newExerciseHtml = "";
    if (data.tipo === "mcq") {
      let alternativasHtml = data.alternativas
        .map(
          ([numero, texto]) =>
            `<input type="radio" name="resposta" id="alt${numero}" value="${numero}" hidden class="alternativa-exercicio" /><label for="alt${numero}" class="botao-alternativa"><span class="numero-alternativa">${numero}</span><span class="texto-alternativa">${texto}</span></label>`
        )
        .join("");
      newExerciseHtml = `<div class="formulario"><div class="exercicio-mcq-layout"><div class="exercicio-mcq-conteudo">${
        data.enunciado
          ? `<p class="exercicio-enunciado">${data.enunciado}</p>`
          : ""
      }${
        data.codigo ? `<pre class="exercicio-codigo">${data.codigo}</pre>` : ""
      }</div><div class="exercicio-mcq-alternativas"><div class="alternativas"><h3>Alternativas</h3>${alternativasHtml}</div></div></div></div>`;
    }
    conteudoWrapper.innerHTML = newExerciseHtml;

    // --- ALTERAÇÃO 2: Usamos a variável com o HTML salvo ---
    baseAcoes.innerHTML = htmlBotoesPadrao;

    initializeEventListeners();
  }

  function updateProgressBar(progressData) {
    const progressBar = document.querySelector(
      ".barra-progresso-preenchimento"
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
        label.classList.add(
          data.correta
            ? "alternativa-correta"
            : "alternativa-correta-nao-marcada"
        );
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
  }

  // DENTRO DO SEU SCRIPT PRINCIPAL

  function updateResponderButtonState() {
    // A MUDANÇA É APENAS NESTA LINHA:
    const responderButton = document.getElementById(
      "botao-responder-exercicio"
    );

    if (!responderButton) return; // Se o botão não existir, a função para.

    // O resto da lógica permanece o mesmo.
    const algumaAlternativaMarcada = form.querySelector(
      'input[type="radio"]:checked'
    );
    responderButton.disabled = !algumaAlternativaMarcada;
  }

  function initializeEventListeners() {
    // PROCURA PELOS NOVOS BOTÕES PELO ID
    const botaoResponder = document.getElementById("botao-responder-exercicio");
    const botaoPular = document.getElementById("botao-pular-exercicio");

    // Adiciona o listener para o clique em "Responder"
    if (botaoResponder) {
      botaoResponder.addEventListener("click", () =>
        enviarAcaoAjax("responder")
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
      ".alternativas, .alternativas-vf"
    );
    if (alternativasDiv)
      alternativasDiv.addEventListener("change", updateResponderButtonState);

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

  if ("{{ sem_vidas|default:'false' }}" === "True") {
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

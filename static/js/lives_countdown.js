document.addEventListener('DOMContentLoaded', () => {
  const widgets = [...document.querySelectorAll('[data-vidas-widget]')];
  if (!widgets.length) return;

  const url = widgets[0].dataset.vidasUrl;
  let vidas = Number(widgets[0].dataset.vidasAtuais);
  let maxVidas = Number(widgets[0].dataset.maxVidas);
  let segundos = Number(widgets[0].dataset.segundosProximaVida);
  let consultando = false;

  function desenhar() {
    for (const widget of widgets) {
      const contador = widget.querySelector('[data-vidas-contador]');
      const tempo = widget.querySelector('[data-vidas-tempo]');
      if (contador) contador.textContent = vidas;
      if (!tempo) continue;
      tempo.hidden = vidas >= maxVidas;
      if (!tempo.hidden) {
        const minutos = Math.floor(segundos / 60);
        const resto = String(segundos % 60).padStart(2, '0');
        tempo.textContent = `+1 em ${minutos}:${resto}`;
        tempo.title = 'Tempo para recuperar a próxima vida';
      }
    }
  }

  async function consultar() {
    if (consultando) return;
    consultando = true;
    try {
      const resposta = await fetch(url, { credentials: 'same-origin', cache: 'no-store' });
      if (!resposta.ok) throw new Error('Falha ao consultar vidas');
      const dados = await resposta.json();
      const estavaSemVidas = vidas === 0;
      vidas = dados.vidas_atuais;
      maxVidas = dados.max_vidas;
      segundos = dados.segundos_proxima_vida;
      desenhar();
      if (estavaSemVidas && vidas > 0) window.dispatchEvent(new Event('vidas:restauradas'));
    } catch {
      segundos = Math.max(segundos, 10);
    } finally {
      consultando = false;
    }
  }

  desenhar();
  window.setInterval(() => {
    if (document.visibilityState !== 'visible' || vidas >= maxVidas) return;
    segundos = Math.max(0, segundos - 1);
    desenhar();
    if (segundos === 0) consultar().catch(() => {});
  }, 1000);
  window.setInterval(() => {
    if (document.visibilityState === 'visible') consultar().catch(() => {});
  }, 60000);
  window.addEventListener('focus', () => consultar().catch(() => {}));
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') consultar().catch(() => {});
  });
  window.addEventListener('vidas:atualizar', () => consultar().catch(() => {}));
});

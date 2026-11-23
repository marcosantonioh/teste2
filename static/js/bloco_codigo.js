document.addEventListener('click', async (event) => {
  const botao = event.target.closest('[data-copiar-codigo]');
  if (!botao) return;

  const editor = botao.closest('.ide-editor');
  const codigo = [...editor.querySelectorAll('.ide-code__conteudo')]
    .map((linha) => linha.textContent)
    .join('\n');

  try {
    await navigator.clipboard.writeText(codigo);
    botao.textContent = 'Copiado!';
    window.setTimeout(() => { botao.textContent = 'Copiar'; }, 1800);
  } catch {
    botao.textContent = 'Não foi possível copiar';
    window.setTimeout(() => { botao.textContent = 'Copiar'; }, 1800);
  }
});

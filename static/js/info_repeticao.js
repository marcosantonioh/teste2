document.addEventListener('DOMContentLoaded', () => {
  const aula = document.querySelector('.aula-repeticao');
  if (!aula) return;

  const etapas = [...aula.querySelectorAll('[data-passo]')];
  const descricao = aula.querySelector('[data-descricao-passo]');
  const botao = aula.querySelector('[data-proximo-passo]');
  const mensagens = [
    'Começamos com i = 0.',
    'i é menor que 3? Sim. Vamos executar.',
    'O programa mostra o valor atual de i.',
    'Somamos 1 a i para preparar a próxima volta.',
    'Voltamos à condição. Quando i chegar a 3, o laço termina.'
  ];
  let passo = 0;

  botao.addEventListener('click', () => {
    passo = (passo + 1) % etapas.length;
    etapas.forEach((etapa, indice) => etapa.classList.toggle('ativo', indice === passo));
    descricao.textContent = mensagens[passo];
    botao.lastElementChild.textContent = passo === etapas.length - 1 ? '↺' : '→';
  });
});

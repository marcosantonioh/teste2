function isMobile() {
  return window.innerWidth <= 768;
}

function voltarParaSidebar() {
  document.querySelector('.sidebar').classList.remove('oculta');
  document.querySelector('.main-content').classList.remove('ativa');
}

document.addEventListener('DOMContentLoaded', () => {
  const layout = document.querySelector('.account-layout');
  const links = [...document.querySelectorAll('.sidebar .nav-link[data-section]')];
  const secoes = [...document.querySelectorAll('.content-section')];
  const sidebar = document.querySelector('.sidebar');
  const conteudo = document.querySelector('.main-content');

  function abrirSecao(nome, atualizarUrl = false) {
    const destino = document.getElementById(`section-${nome}`);
    if (!destino) return;

    links.forEach(link => {
      const ativa = link.dataset.section === nome;
      link.classList.toggle('active', ativa);
      if (ativa) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    secoes.forEach(secao => secao.classList.toggle('active', secao === destino));
    if (isMobile()) {
      sidebar.classList.add('oculta');
      conteudo.classList.add('ativa');
    }
    if (atualizarUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set('secao', nome);
      window.history.pushState({ secao: nome }, '', url);
    }
  }

  links.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    abrirSecao(link.dataset.section, true);
  }));

  window.addEventListener('popstate', () => {
    abrirSecao(new URLSearchParams(window.location.search).get('secao') || 'informacoes');
  });

  const abaInicial = layout.dataset.abaInicial || 'informacoes';
  if (isMobile() && abaInicial === 'informacoes') {
    links.find(link => link.dataset.section === abaInicial)?.classList.add('active');
  } else {
    abrirSecao(abaInicial);
  }

  const preview = document.getElementById('preview-img');
  document.querySelectorAll('input[name="avatar"]').forEach(input => {
    input.addEventListener('change', () => {
      if (preview && input.checked && input.dataset.avatarUrl) {
        preview.src = input.dataset.avatarUrl;
      }
    });
  });
});

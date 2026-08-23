  function isMobile() {
    return window.innerWidth <= 768;
  }

  function setupFotoPreview() {
    const inputFoto = document.getElementById('id_foto');
    const previewImg = document.getElementById('preview-img');

    if (inputFoto && previewImg) {
      inputFoto.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function (e) {
            previewImg.src = e.target.result;
          };
          reader.readAsDataURL(file);
        }
      });
    }
  }

  function voltarParaSidebar() {
    // Oculta todas as seções
    document.querySelectorAll('.content-section').forEach(section => {
      section.classList.remove('active');
    });

    // Mostra a sidebar e esconde o conteúdo principal (modo mobile)
    document.querySelector('.sidebar').classList.remove('oculta');
    document.querySelector('.main-content').classList.remove('ativa');
  }

  document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    // Clique nos links da sidebar
    navLinks.forEach(link => {
      // O logout é uma navegação real; não deve ser tratado como aba de configuração.
      if (link.classList.contains('nav-link-logout')) {
        return;
      }

      link.addEventListener('click', function (e) {
        e.preventDefault();

        // Ativa o link clicado
        navLinks.forEach(l => l.classList.remove('active'));
        this.classList.add('active');

        // Mostra apenas a seção correta
        const sectionId = this.getAttribute('data-section');
        contentSections.forEach(sec => sec.classList.remove('active'));
        const targetSection = document.getElementById('section-' + sectionId);
        if (targetSection) {
          targetSection.classList.add('active');
        }

        // Executa setup da foto se for "informações"
        if (sectionId === 'informacoes') {
          setupFotoPreview();
        }

        // No mobile: esconde a sidebar e mostra o conteúdo
        if (isMobile()) {
          sidebar.classList.add('oculta');
          mainContent.classList.add('ativa');
        }
      });
    });

    // Setup inicial
    setupFotoPreview();
  });

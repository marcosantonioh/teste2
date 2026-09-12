  function isMobile() {
    return window.innerWidth <= 768;
  }

  function setupAvatarPreview() {
    const avatarInputs = document.querySelectorAll('input[name="avatar"]');
    const previewImg = document.getElementById('preview-img');

    avatarInputs.forEach(input => {
      input.addEventListener('change', function () {
        if (this.checked && this.dataset.avatarUrl) {
          previewImg.src = this.dataset.avatarUrl;
        }
      });
    });
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

        // No mobile: esconde a sidebar e mostra o conteúdo
        if (isMobile()) {
          sidebar.classList.add('oculta');
          mainContent.classList.add('ativa');
        }
      });
    });

    // Setup inicial
    setupAvatarPreview();
  });

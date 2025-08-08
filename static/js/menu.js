// Menu lateral toggle
function abrirMenu() {
  const menu = document.getElementById('menuLateral');
  const estaAberto = menu.style.left === '0px';

  if (estaAberto) {
    menu.style.left = '-250px';
    document.removeEventListener('click', fecharForaDoMenu);
  } else {
    menu.style.left = '0px';
    setTimeout(() => {
      document.addEventListener('click', fecharForaDoMenu);
    }, 10);
  }
}

function fecharForaDoMenu(event) {
  const menu = document.getElementById('menuLateral');
  const botaoMenu = document.getElementById('botaoMenu');

  if (!menu.contains(event.target) && !botaoMenu.contains(event.target)) {
    menu.style.left = '-250px';
    document.removeEventListener('click', fecharForaDoMenu);
  }
}











// MENU INDEX - Com submenus

// Submenu toggle lateral (caso use em outro lugar)
document.querySelectorAll('.toggle-submenu').forEach(button => {
  button.addEventListener('click', () => {
    const submenu = button.nextElementSibling;
    if (submenu) {
      submenu.classList.toggle('ativo');
    }
  });
});

// Abrir e fechar submenus flutuantes
function abrirSubmenu(tipo) {
  document.querySelectorAll('.submenu-flutuante').forEach(sub => {
    if (sub.id === `submenu-${tipo}`) {
      sub.classList.toggle('ativo');
    } else {
      sub.classList.remove('ativo');
    }
  });
}

// Scroll suave ao clicar num item
function scrollParaElemento(id) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
  document.querySelectorAll('.submenu-flutuante').forEach(sub => sub.classList.remove('ativo'));
}

// Fecha submenus ao clicar fora
document.addEventListener('click', function(e) {
  if (
    !e.target.closest('.menu-scroll-flutuante') &&
    !e.target.closest('.submenu-flutuante') &&
    !e.target.closest('.menu-toggle')
  ) {
    // Fecha submenus
    document.querySelectorAll('.submenu-flutuante').forEach(sub => sub.classList.remove('ativo'));
    // Fecha menu principal
    menuFlutuante.classList.remove('ativo');
    toggleBtn.classList.remove('ativo');
  }
});

// Toggle do menu principal (botão preto)
const toggleBtn = document.getElementById('menuToggle');
const menuFlutuante = document.getElementById('menuScrollFlutuante');

toggleBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  const ativo = menuFlutuante.classList.toggle('ativo');
  toggleBtn.classList.toggle('ativo', ativo);
});




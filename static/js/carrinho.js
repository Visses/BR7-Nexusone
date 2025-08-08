// ==== UTILITÁRIOS DE PREÇO ==== //
function parsePreco(precoStr) {
  if (typeof precoStr === "number") return precoStr;
  if (!precoStr || typeof precoStr !== "string") return 0;

  const precoFormatado = precoStr.replace(/\./g, '').replace(',', '.');
  return parseFloat(precoFormatado) || 0;
}


function formatarPreco(valor) {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ==== LOCALSTORAGE ==== //
function pegarCarrinho() {
  return JSON.parse(localStorage.getItem('carrinho')) || {};
}

function salvarCarrinho(carrinho) {
  localStorage.setItem('carrinho', JSON.stringify(carrinho));
}

// ==== ADICIONAR PRODUTO ==== //
// ==== ADICIONAR PRODUTO COM LINK E TIPO/CATEGORIA/SUBCATEGORIA ==== //
function adicionarCarrinho(event, id, nome, preco, tipo, categoria, subcategoria, disponibilidade) {
  event.preventDefault();

  const tamanho = document.getElementById('tamanho')?.value || '';
  const cor = document.getElementById('cor')?.value || '';
  const imagem = document.getElementById('imagem-carrossel')?.src || '';
  const link = window.location.href;

  const carrinho = pegarCarrinho();
  const chaveProduto = `${id}_${tamanho}_${cor}`;

  if (carrinho[chaveProduto]) {
    carrinho[chaveProduto].quantidade += 1;
  } else {
    carrinho[chaveProduto] = {
      nome,
      preco: parsePreco(preco),
      quantidade: 1,
      tamanho,
      cor,
      imagem,
      link,
      tipo,
      categoria,
      subcategoria,
      disponibilidade
    };
  }

  salvarCarrinho(carrinho);
  alert(`${nome} (Tam: ${tamanho || 'Único'}, Cor: ${cor || 'Único'}) adicionado ao carrinho!`);
  atualizarBadgeCarrinho();
}



// ==== ATUALIZAR BADGE ==== //
function atualizarBadgeCarrinho() {
  const carrinho = pegarCarrinho();
  const badge = document.getElementById('badge-carrinho');
  const totalItens = Object.values(carrinho).reduce((acc, item) => acc + item.quantidade, 0);

  if (badge) {
    if (totalItens > 0) {
      badge.textContent = totalItens;
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  }
}

// ==== ABRIR MODAL DO CARRINHO ==== //
function abrirCarrinho() {
  const carrinho = pegarCarrinho();
  const lista = document.getElementById('lista-carrinho');
  lista.innerHTML = '';

  let total = 0;
  for (const chave in carrinho) {
    const item = carrinho[chave];
    const subtotal = item.preco * item.quantidade;
    total += subtotal;

    const li = document.createElement('li');
    li.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <img src="${item.imagem}" alt="${item.nome}" style="width:60px;height:60px;border-radius:5px;object-fit:cover;">
        <div style="flex-grow:1;">
          <div><strong>${item.nome}</strong></div>
          <div>Tam: ${item.tamanho || 'Único'} | Cor: ${item.cor || 'Único'}</div>
          <div>Qtd: ${item.quantidade} x R$ ${formatarPreco(item.preco)}</div>
          <div>Subtotal: R$ ${formatarPreco(subtotal)}</div>
        </div>
        <button class="remove-btn" data-id="${chave}" style="background:red;color:white;border:none;border-radius:4px;padding:5px 8px;cursor:pointer;">✕</button>
      </div>
    `;
    lista.appendChild(li);
  }

  document.getElementById('total-carrinho').textContent = 'Total: R$ ' + formatarPreco(total);
  document.getElementById('modal-carrinho').style.display = 'flex';
}

// ==== REMOVER ITEM ==== //
function removerDoCarrinho(chave) {
  const carrinho = pegarCarrinho();
  delete carrinho[chave];
  salvarCarrinho(carrinho);
  atualizarBadgeCarrinho();
  abrirCarrinho();
}

// ==== FECHAR MODAL ==== //
function fecharCarrinho() {
  const modal = document.getElementById("modal-carrinho");
  modal.style.display = "none";
}

// ==== FECHAR MODAL FORA ==== //
window.addEventListener('click', function (event) {
  const modal = document.getElementById("modal-carrinho");
  if (event.target === modal) {
    modal.style.display = "none";
  }
});

// ==== BOTÃO REMOVER ==== //
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('remove-btn')) {
    const chave = e.target.getAttribute('data-id');
    removerDoCarrinho(chave);
  }
});

// ==== GERAR RESUMO NA TELA FINALIZAR ==== //
function gerarResumoPedido() {
  const listaProdutos = document.getElementById('lista-produtos');
  const totalSpan = document.getElementById('total');

  if (!listaProdutos || !totalSpan) return;

  const carrinho = pegarCarrinho();
  let total = 0;

  listaProdutos.innerHTML = '';

  for (const chave in carrinho) {
    const item = carrinho[chave];
    const subtotal = item.preco * item.quantidade;
    total += subtotal;

    const div = document.createElement('div');
div.innerHTML = `
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
    <img src="${item.imagem}" alt="${item.nome}" style="width:60px;height:60px;border-radius:5px;object-fit:cover;">
    <div>
      <a href="${item.link}" target="_blank" style="font-weight:bold;text-decoration:underline;">${item.nome}</a>
      ${item.tamanho ? ' - Tam: ' + item.tamanho : ''} 
      ${item.cor ? ' - Cor: ' + item.cor : ''}
      <br>Qtd: ${item.quantidade} | R$ ${formatarPreco(subtotal)}
    </div>
  </div>
`;
listaProdutos.appendChild(div);

  }

  totalSpan.innerText = 'R$ ' + formatarPreco(total);
}

// ==== ENVIAR PEDIDO VIA WHATSAPP ==== //
document.addEventListener('DOMContentLoaded', function () {
  atualizarBadgeCarrinho();

  const formFinalizar = document.getElementById('form-finalizar');
  if (formFinalizar) {
    gerarResumoPedido();

    formFinalizar.addEventListener('submit', function (e) {
      e.preventDefault();

      const dados = Object.fromEntries(new FormData(formFinalizar).entries());
      const carrinho = pegarCarrinho();

      if (Object.keys(carrinho).length === 0) {
        alert('Seu carrinho está vazio!');
        return;
      }

      let mensagem = `⚽ *Pedido BR7 CHUTEIRAS concluído!!*\n\n`;

for (const chave in carrinho) {
  const item = carrinho[chave];
  const subtotal = item.preco * item.quantidade;

  let detalhes = (item.categoria || '').toUpperCase();
  if (item.subcategoria) detalhes += ` / ${item.subcategoria.toUpperCase()}`;

  mensagem += `*${(item.tipo || 'Produto').toUpperCase()}*`;
  if (detalhes) mensagem += ` (${detalhes})`;
  if (item.link) mensagem += `: ${item.link}\n`;

  mensagem += `Nome: ${item.nome}\n`;
  if (item.tamanho) mensagem += `Tamanho: ${item.tamanho}\n`;
  if (item.cor) mensagem += `Cor: ${item.cor}\n`;
  mensagem += `Quantidade: ${item.quantidade}\n`;
  mensagem += `Valor: R$ ${formatarPreco(subtotal)}\n\n`;
}



      mensagem += `👤*Informações do Cliente*\n`;
      mensagem += `*Nome:* ${dados.nome}\n`;
      if (dados.cpf) mensagem += `CPF: ${dados.cpf}\n`;
      mensagem += `*Estado:* ${dados.estado}\n`;
      mensagem += `*Cidade:* ${dados.cidade}\n`;
      mensagem += `*Bairro:* ${dados.bairro}\n`;
      mensagem += `*Rua:* ${dados.rua}\n`;
      mensagem += `*Numero da residência:* ${dados.numero}\n`;
      if (dados.complemento) mensagem += `*Complemento:* ${dados.complemento}\n`;
      mensagem += `*Cep:* ${dados.cep}\n\n`;

      mensagem += `💰 *Forma de pagamento*\n${dados.pagamento}\n\n`;
      mensagem += `📦 *Forma de retirada*\n${dados.retirada}\n\n`;

      // Calcular total geral
      let total = 0;
      for (const chave in carrinho) {
        total += carrinho[chave].preco * carrinho[chave].quantidade;
      }
      mensagem += `*Total:* R$ ${formatarPreco(total)}\n`;

      const textoFinal = encodeURIComponent(mensagem);
      const numeroWpp = '11947629000'; // Seu número WhatsApp

      window.open(`https://wa.me/${numeroWpp}?text=${textoFinal}`, '_blank');

      // Se quiser limpar o carrinho após enviar, descomente:
      // localStorage.removeItem('carrinho');
    });
  }
});





























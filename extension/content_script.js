function getGenericItems() {
  // This function contains the old, generic scraping logic.
  // It's a combination of extractCartItems and extractSingleProduct from the previous version.
  function extractCartItems() {
    const items = [];
    const genericSelectors = [
      '[data-test="cart-item"]',
      '.cart-item',
      '.checkout-item',
      '.line-item',
      '.product',
    ];

    let nodes = [];
    genericSelectors.forEach(
      (s) => (nodes = nodes.concat(Array.from(document.querySelectorAll(s))))
    );

    nodes = Array.from(new Set(nodes));

    nodes.slice(0, 50).forEach((node) => {
      try {
        let name = '';
        const span = node.querySelector('span');
        if (span && span.textContent.trim().length > 2) {
            name = span.textContent.trim();
        } else {
            const text = node.textContent.trim().replace(/\s+/g, " ");
            name = text.split("\n")[0].slice(0, 120) || text.slice(0, 120);
        }

        const qtyMatch = node.textContent.match(/\b(\d+)\b/);
        const qty = qtyMatch ? parseInt(qtyMatch[1], 10) : 1;

        items.push({ name: name, quantity: qty });
      } catch (e) {
        /*ignore*/
      }
    });

    const filteredItems = items.filter(item => {
        const lowerCaseName = item.name.toLowerCase();
        if (lowerCaseName.includes('add to cart')) return false;
        if (lowerCaseName.includes('previous page')) return false;
        if (lowerCaseName.includes('actionid')) return false;
        if (lowerCaseName.length < 3) return false;
        return true;
    });

    return filteredItems;
  }

  function extractSingleProduct() {
    const product = {};
    const h1 = document.querySelector('h1');
    if (h1) {
        product.name = h1.textContent.trim();
    } else {
        product.name = document.title.split('|')[0].trim();
    }
    product.quantity = 1;

    const bodyText = document.body.innerText;
    const upcMatch = bodyText.match(/\b(\d{12,13})\b/);
    if (upcMatch) {
      product.upc = upcMatch[1];
    }

    if (product.name) {
      return [product];
    }
    return [];
  }

  let items = extractCartItems();
  if (items.length === 0) {
    items = extractSingleProduct();
  }
  return items;
}


async function main() {
  setTimeout(async () => {
    try {
      const response = await fetch(chrome.runtime.getURL('scrapers.json'));
      const scrapers = await response.json();
      const hostname = window.location.hostname;

      let items = [];
      const config = scrapers[hostname];

      if (config) {
        // Site-specific scraper logic
        const itemNodes = document.querySelectorAll(config.itemSelector);
        itemNodes.forEach(node => {
          const nameNode = node.querySelector(config.nameSelector);
          const quantityNode = node.querySelector(config.quantitySelector);
          const upcNode = node.querySelector(config.upcSelector);

          if (nameNode) {
            const item = {
              name: nameNode.textContent.trim(),
              quantity: quantityNode ? parseInt(quantityNode.textContent, 10) : 1,
            };

            if (upcNode) {
              if (config.upcType === 'asin') {
                item.upc = upcNode.dataset.asin;
              } else {
                // Future placeholder for other ID types
                item.upc = upcNode.textContent.trim();
              }
            }
            items.push(item);
          }
        });
      }

      // If specific scraper fails or no config exists, use the generic one
      if (items.length === 0) {
        items = getGenericItems();
      }

      window.__FLINTpro_cart = items;
      console.info("FLINTpro: cart discovered", window.__FLINTpro_cart);

    } catch (e) {
      console.warn("FLINTpro scraper error", e);
      // Fallback to generic scraper in case of any error
      window.__FLINTpro_cart = getGenericItems();
      console.info("FLINTpro: cart discovered (fallback)", window.__FLINTpro_cart);
    }
  }, 2000); // Wait 2 seconds for the page to load
}

main();

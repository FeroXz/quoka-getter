class QuokaCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Entity is required");
    }
    this._config = config;
    this.render();
  }

  connectedCallback() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 3;
  }

  render() {
    if (!this.shadowRoot || !this._config || !this._hass) {
      return;
    }

    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card>Entity ${this._config.entity} not found.</ha-card>`;
      return;
    }

    const listings = stateObj.attributes.listings || [];
    const cardTitle = this._config.title || stateObj.attributes.friendly_name || "Quoka Listings";

    const style = `
      <style>
        :host {
          display: block;
        }
        .actions {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 12px;
        }
        .refresh-button {
          background: var(--primary-color);
          border: none;
          border-radius: 4px;
          color: var(--text-primary-color, #fff);
          cursor: pointer;
          font: inherit;
          padding: 6px 12px;
          transition: filter 0.2s ease;
        }
        .refresh-button:hover {
          filter: brightness(0.95);
        }
        .container {
          display: grid;
          gap: 12px;
        }
        .listing {
          display: grid;
          grid-template-columns: 120px 1fr;
          gap: 12px;
          align-items: start;
        }
        .listing img,
        .placeholder {
          width: 120px;
          height: 120px;
          object-fit: cover;
          border-radius: 8px;
          background: var(--divider-color);
        }
        .listing .details {
          display: grid;
          gap: 6px;
        }
        .listing a {
          color: var(--primary-color);
          text-decoration: none;
          font-weight: bold;
        }
        .listing a:hover {
          text-decoration: underline;
        }
        .price {
          font-size: 1.1em;
          font-weight: bold;
        }
        .meta {
          color: var(--secondary-text-color);
        }
      </style>
    `;

    const content = listings
      .map((item) => {
        const image = item.image
          ? `<img src="${item.image}" alt="${item.title}">`
          : `<div class="placeholder"></div>`;
        const price = item.price ? `<div class="price">${item.price}</div>` : "";
        const location = item.location ? `<div class="meta">${item.location}</div>` : "";
        const published = item.published ? `<div class="meta">${new Date(item.published).toLocaleString()}</div>` : "";
        return `
          <div class="listing">
            ${image}
            <div class="details">
              <a href="${item.url}" target="_blank" rel="noreferrer">${item.title}</a>
              ${price}
              ${location}
              ${published}
            </div>
          </div>
        `;
      })
      .join("");

    this.shadowRoot.innerHTML = `
      <ha-card header="${cardTitle}">
        <div class="actions">
          <button class="refresh-button" type="button">Jetzt aktualisieren</button>
        </div>
        <div class="container">
          ${content || `<div class="meta">Keine Ergebnisse gefunden.</div>`}
        </div>
      </ha-card>
      ${style}
    `;

    const refreshButton = this.shadowRoot.querySelector(".refresh-button");
    if (refreshButton) {
      refreshButton.addEventListener("click", () => {
        if (!this._hass) {
          return;
        }
        this._hass.callService("quoka", "refresh", {
          entity_id: this._config.entity,
        });
      });
    }
  }
}

customElements.define("quoka-card", QuokaCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "quoka-card",
  name: "Quoka Card",
  description: "Zeigt Ergebnisse der Quoka Getter Integration an."
});

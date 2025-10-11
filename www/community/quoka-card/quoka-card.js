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
    const language = this._hass.locale?.language || window.navigator?.language || "de-DE";
    const searchTerms = Array.isArray(stateObj.attributes.search_terms)
      ? stateObj.attributes.search_terms
      : [];
    const categories = Array.isArray(stateObj.attributes.categories)
      ? stateObj.attributes.categories
      : [];

    const formatDateTime = (value) => {
      if (!value) {
        return null;
      }
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return null;
      }
      try {
        return new Intl.DateTimeFormat(language, {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(date);
      } catch (error) {
        return date.toLocaleString();
      }
    };

    const escapeHtml = (value) => {
      if (value === null || value === undefined) {
        return "";
      }
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    };

    const style = `
      <style>
        :host {
          display: block;
        }
        .card-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .card-toolbar {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .actions {
          display: flex;
          gap: 8px;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
        }
        .summary {
          color: var(--secondary-text-color);
          font-size: 0.9rem;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .summary strong {
          color: var(--primary-text-color);
          font-weight: 600;
        }
        .pills {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .pill {
          background: rgba(0, 0, 0, 0.08);
          color: var(--primary-text-color);
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 0.75rem;
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
        .refresh-button:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
        }
        .container {
          display: grid;
          gap: 16px;
        }
        .listing {
          display: grid;
          grid-template-columns: minmax(0, 120px) 1fr;
          gap: 16px;
          align-items: stretch;
          background: var(--card-background-color, rgba(0, 0, 0, 0.04));
          border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
          border-radius: 12px;
          padding: 12px;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .listing:hover {
          border-color: var(--primary-color);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
        }
        .thumb {
          position: relative;
          width: 100%;
          max-width: 120px;
          aspect-ratio: 1 / 1;
          border-radius: 10px;
          overflow: hidden;
          background: linear-gradient(135deg, rgba(0,0,0,0.08), rgba(0,0,0,0.02));
        }
        .thumb img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
        }
        .thumb .fallback {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--secondary-text-color);
          font-size: 0.85rem;
        }
        .details {
          display: flex;
          flex-direction: column;
          gap: 8px;
          min-width: 0;
        }
        .title {
          font-weight: 600;
          font-size: 1.05rem;
          color: var(--primary-text-color);
          text-decoration: none;
          line-height: 1.4;
        }
        .title:hover,
        .title:focus {
          text-decoration: underline;
        }
        .meta-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .meta {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: var(--secondary-text-color);
          font-size: 0.85rem;
        }
        .price {
          font-weight: 600;
          color: var(--primary-color);
          background: rgba(0, 0, 0, 0.05);
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 0.9rem;
        }
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 24px;
          text-align: center;
          border: 1px dashed var(--divider-color, rgba(0,0,0,0.2));
          border-radius: 12px;
          color: var(--secondary-text-color);
          background: rgba(0, 0, 0, 0.02);
        }
        .empty-state strong {
          color: var(--primary-text-color);
        }
        @media (max-width: 600px) {
          .listing {
            grid-template-columns: 1fr;
          }
          .thumb {
            max-width: none;
            width: 100%;
          }
          .actions {
            flex-direction: column;
            align-items: stretch;
          }
          .actions .refresh-button {
            width: 100%;
          }
        }
      </style>
    `;

    const hasSummaryContent = searchTerms.length > 0 || categories.length > 0;
    const summary = this._config.hide_summary || !hasSummaryContent
      ? ""
      : `
          <div class="summary">
            ${searchTerms.length
              ? `<div>
                  <strong>Suchbegriffe:</strong>
                  <div class="pills">
                    ${searchTerms
                      .map((term) => `<span class="pill">${escapeHtml(term)}</span>`)
                      .join("")}
                  </div>
                </div>`
              : ""}
            ${categories.length
              ? `<div>
                  <strong>Kategorien:</strong>
                  <div class="pills">
                    ${categories
                      .map((category) => `<span class="pill">${escapeHtml(category)}</span>`)
                      .join("")}
                  </div>
                </div>`
              : ""}
          </div>
        `;

    const content = listings
      .map((item) => {
        const title = escapeHtml(item.title);
        const image = item.image
          ? `<img src="${item.image}" alt="${title}">`
          : "";
        const price = item.price ? `<span class="price">${escapeHtml(item.price)}</span>` : "";
        const location = item.location
          ? `<span class="meta" title="Ort">📍 ${escapeHtml(item.location)}</span>`
          : "";
        const publishedText = formatDateTime(item.published);
        const published = publishedText
          ? `<span class="meta" title="Veröffentlicht">🕒 ${publishedText}</span>`
          : "";
        return `
          <article class="listing">
            <div class="thumb">
              ${image || '<div class="fallback">Kein Bild</div>'}
            </div>
            <div class="details">
              <a class="title" href="${item.url}" target="_blank" rel="noreferrer">${title}</a>
              <div class="meta-row">
                ${price}
                ${location}
                ${published}
              </div>
            </div>
          </article>
        `;
      })
      .join("");

    this.shadowRoot.innerHTML = `
      <ha-card header="${cardTitle}">
        <div class="card-content">
          <div class="card-toolbar">
            <div class="actions">
              ${summary}
              <button class="refresh-button" type="button">Jetzt aktualisieren</button>
            </div>
          </div>
          <div class="container">
            ${
              content ||
              `<div class="empty-state">
                <strong>Keine Ergebnisse gefunden</strong>
                <span>Bitte überprüfe deine Suchbegriffe oder Kategorien.</span>
              </div>`
            }
          </div>
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

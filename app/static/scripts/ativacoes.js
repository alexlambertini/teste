document.addEventListener("alpine:init", () => {
  console.log("Alpine.js está pronto - Registrando componentes");

  Alpine.data("modalAtivacao", () => ({
    isVisible: false,
    init() {
      console.log("ModalAtivacao inicializado");
      Alpine.store("modalAtivacao", this);
    },
    open() {
      this.isVisible = true;
      document.body.style.overflow = "hidden";
    },
    close() {
      this.isVisible = false;
      document.body.style.overflow = "";
    },
    async submit() {
      const app = Alpine.store("app");
      if (app) {
        await app.submitForm();
        this.close();
      }
    },
  }));

  Alpine.data("modalDesativacao", () => ({
    isVisible: false,
    init() {
      Alpine.store("modalDesativacao", this);
    },
    open() {
      this.isVisible = true;
      document.body.style.overflow = "hidden";
    },
    close() {
      this.isVisible = false;
      document.body.style.overflow = "";
    },
    async submit() {
      const app = Alpine.store("app");
      if (app) {
        await app.submitDesativadoForm();
        this.close();
      }
    },
  }));

  Alpine.data("app", () => ({
    nomeError: false,
    baseUrl: "http://localhost:8000",
    ativados: [],
    desativados: [],
    tecnicos: [],
    categorias: [],
    selectedClient: null,
    tecnicosSelecionados: [],
    formData: {
      nome: "",
      sobrenome: "",
      empresa: "",
      tecnologia: "",
      tecnicos: [],
      taxa: "",
      data_ativacao: new Date().toISOString().split("T")[0],
      isento: false,
      endereco: "",
    },
    desativadoForm: {
      ativado_id: null,
      nome: "",
      motivo: "",
      categoria_id: null,
      equipamento_retirado: "sim",
    },

    init() {
      this.fetchData();
      this.setupWebSocket();
      Alpine.store("app", this);
    },

    async fetchData() {
      try {
        const [ativadosRes, desativadosRes, tecnicosRes, categoriasRes] = await Promise.all([
          fetch(`${this.baseUrl}/work/api/ativados`),
          fetch(`${this.baseUrl}/work/api/desativados`),
          fetch(`${this.baseUrl}/work/api/tecnicos`),
          fetch(`${this.baseUrl}/work/api/categorias`),
        ]);

        const [ativados, desativados, tecnicos, categorias] = await Promise.all([
          ativadosRes.json(),
          desativadosRes.json(),
          tecnicosRes.json(),
          categoriasRes.json(),
        ]);

        // Usa diretamente os dados do backend que já estão ordenados
        this.ativados = Array.isArray(ativados) ? ativados : [];
        this.desativados = Array.isArray(desativados) ? desativados : [];

        // Ordenação apenas para técnicos e categorias (caso queira manter visual consistente)
        this.tecnicos = Array.isArray(tecnicos)
          ? tecnicos.sort((a, b) => a.nome.localeCompare(b.nome))
          : [];

        this.categorias = Array.isArray(categorias)
          ? categorias.sort((a, b) => a.nome.localeCompare(b.nome))
          : [];
      } catch (error) {
        console.error("Erro ao carregar dados:", error);
        Swal.fire({ icon: "error", title: "Erro", text: "Erro ao buscar dados." });
      }
    },

    showModal(client = null) {
      this.selectedClient = client;
      if (client) {
        this.formData = { ...client, tecnicos: client.tecnicos.map((t) => t.id) };
        this.tecnicosSelecionados = client.tecnicos.map((t) => t.id);
      } else {
        this.formData = {
          nome: "",
          sobrenome: "",
          empresa: "",
          tecnologia: "",
          tecnicos: [],
          taxa: "",
          data_ativacao: new Date().toISOString().split("T")[0],
          isento: false,
          endereco: "",
        };
        this.tecnicosSelecionados = [];
      }

      const modal = Alpine.store("modalAtivacao");
      if (modal) modal.open();
    },

    validarEndereco(endereco) {
      return endereco.trim().length >= 5;
    },

    async submitForm() {
      if (!this.validarEndereco(this.formData.endereco || "")) {
        return Swal.fire("Erro", "Endereço inválido.", "error");
      }

      const taxa = this.validarTaxa();
      if (taxa.error) {
        return Swal.fire("Erro", taxa.error, "error");
      }

      try {
        const payload = {
          ...this.formData,
          taxa: this.formData.isento ? null : taxa.valor,
          data_ativacao: new Date(this.formData.data_ativacao).toISOString().split("T")[0],
          tecnicos: this.formData.tecnicos.map(Number),
        };

        const url = this.selectedClient
          ? `${this.baseUrl}/work/api/ativados/${this.selectedClient.id}`
          : `${this.baseUrl}/work/api/ativados`;

        const method = this.selectedClient ? "PUT" : "POST";

        const res = await fetch(url, {
          method,
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": this.getCSRFToken(),
          },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("Erro ao salvar cliente");

        await Swal.fire(
          "Sucesso!",
          this.selectedClient ? "Cliente atualizado" : "Cliente salvo",
          "success"
        );
        this.fetchData();
      } catch (err) {
        console.error(err);
        Swal.fire("Erro", err.message, "error");
      }
    },

    getTecnicoById(id) {
      return this.tecnicos.find((t) => String(t.id) === String(id));
    },

    getCSRFToken() {
      const token = document.cookie.match(/csrftoken=([^;]+)/);
      return token ? token[1] : "";
    },

    validarTaxa() {
      if (this.formData.isento || !this.formData.taxa) return { valor: null };
      const valor = parseFloat(this.formData.taxa.toString().replace("R$", "").replace(",", "."));
      return isNaN(valor) ? { error: "Taxa inválida" } : { valor };
    },

    setupWebSocket() {
      const protocol = location.protocol === "https:" ? "wss://" : "ws://";
      const socket = new WebSocket(`${protocol}${location.host}/ws/ativados/`);

      socket.onmessage = ({ data }) => {
        try {
          const payload = JSON.parse(data);
          if (payload.action === "refresh") {
            this.fetchData();
            Swal.fire("Atualizado", payload.message, "success");
          }
        } catch (e) {
          console.error("Erro WebSocket:", e);
        }
      };

      socket.onclose = () => setTimeout(() => this.setupWebSocket(), 5000);
      socket.onerror = (e) => console.error("Erro socket:", e);
    },
  }));
});

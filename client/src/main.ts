import { createApp } from "vue";
import App from "./App.vue";
import PrimeVue from "primevue/config";
import { router } from "./router";

const app = createApp(App)
	.use(PrimeVue)
	.use(router)
	.mount("#app");
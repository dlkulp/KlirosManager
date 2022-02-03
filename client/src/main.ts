import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";

import "bootstrap-dark-5/dist/css/bootstrap-dark.min.css";
import "bootstrap";

import { library } from "@fortawesome/fontawesome-svg-core";
import { faHouse, faAt, faArrowUpFromBracket, faMagnifyingGlass, faUserGroup, faLayerGroup, faBars } from "@fortawesome/free-solid-svg-icons";
//import { faAt } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faHouse, faAt, faArrowUpFromBracket, faMagnifyingGlass, faUserGroup, faLayerGroup, faBars);

const app: any = createApp(App)
	.use(router)
	.component("font-awesome-icon", FontAwesomeIcon)
	.mount("#app");
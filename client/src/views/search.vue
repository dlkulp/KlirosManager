<script setup lang="ts">
import Grid from "../components/grid.vue";
import {ref, watch, Ref, onMounted} from "vue";
import { RouterLink } from "vue-router";
import {debouncedRef} from "../helpers/helpers";
import kInput from "../components/forms/kInput.vue";
import kCard from "../components/cards/kCard.vue";

import comeWorship from "../assets/come worship.png";
import ourFather from "../assets/Our Father.png";
import alleluia from "../assets/Alleluia.png";
import ode9 from "../assets/AdventOde9.jpg";
import angelCried from "../assets/Angel Cried.png";

const searchQuery = debouncedRef("");
const results: Ref<any[]> = ref([]);

watch(searchQuery, (query: string, prevQuery: string) => {
	const searchBox = document.querySelector("#searchBox");
	const resultsBox = document.querySelector("#results");
	const emptyMessage = document.querySelector("#empty");
	if (query.length && searchBox) {
		// Slide searchbox up
		searchBox.classList.add("searchBoxQuery");
		searchBox.classList.remove("searchBoxEmpty");
		// Search data
		results.value = data.value.filter((x: any) => {
			let ret = x.title.toLowerCase().includes(query.toLowerCase());
			for (let key of Object.keys(x.metaData))
				ret = ret || `${key.toLowerCase()} ${(x.metaData as any)[key].toString().toLowerCase()}`.includes(query.toLowerCase());
			return ret;
		});

		if (results.value.length == 0) {
			// No search results
			emptyMessage?.classList.add("display")
			resultsBox?.classList.add("searchResultsEmpty");
			resultsBox?.classList.remove("searchResultsShow");
		}
		else {
			// Show results
			emptyMessage?.classList.remove("display")
			resultsBox?.classList.add("searchResultsShow");
			resultsBox?.classList.remove("searchResultsEmpty");
		}
	}
	else {
		// Search box cleared
		emptyMessage?.classList.remove("display")
		searchBox?.classList.add("searchBoxEmpty");
		searchBox?.classList.remove("searchBoxQuery");
		resultsBox?.classList.add("searchResultsEmpty");
		resultsBox?.classList.remove("searchResultsShow");
	}

	// Set url
	window.history.pushState({}, "Search", `?q=${query}`)
});

onMounted(() => {
	if (window.location.search.includes("?q="))
		searchQuery.value = window?.location.search.split("?")[1]?.split("&").find(x=>x.includes("q"))?.split("=")[1] || "";
});

// Temp data for testing UI
const data: Ref<any> = ref([{
	id: "0",
	title: "O Come Let Us Worship",
	img: {url: comeWorship, alt:"O Come Let Us Worship Music"},
	metaData: {
		"Tone Set": "Bulgarian",
		"Tone": 6,
		"Chorus": "mixed",
		"Parts": 3,
		"Service": ["Liturgy"],
		"Language": "English",
		"Part of Service": "Entrance Hymn",
		"Feast": ""
	}
}, {
	id: "1",
	title: "Our Father",
	img: {url: ourFather, alt: "Our Father Music"},
	metaData: {
		"Tone Set": "Strochnoi",
		"Tone": 2,
		"Chorus": "Mixed",
		"Parts": 3,
		"Service": ["Liturgy"],
		"Language": "English",
		"Part of Service": "Our Father",
		"Feast": ""
	}
}, {
	id: "2",
	title: "Alleluia",
	img: {url: alleluia, alt: "Alleluia Music"},
	metaData: {
		"Tone Set": "Znamenny",
		"Tone": 5,
		"Chorus": "Mixed",
		"Parts": 4,
		"Service": ["Liturgy"],
		"Language": "English",
		"Part of Service": "Alleluia",
		"Feast": ""
	}
}, {
	id: "3",
	title: "Ode 9 - Advent",
	img: {url: ode9, alt: "Ode 9 Music"},
	metaData: {
		"Tone Set": "",
		"Tone": "",
		"Chorus": "Mixed",
		"Parts": 4,
		"Service": ["Matins"],
		"Language": "English",
		"Part of Service": "Matins Canon",
		"Feast": "Nativity of the Lord"
	}
}, {
	id: "4",
	title: "The Angel Cried",
	img: {url: angelCried, alt: "The Angel Cried Music"},
	metaData: {
		"Tone Set": "",
		"Tone": "",
		"Chorus": "Mixed",
		"Parts": 4,
		"Service": ["Liturgy"],
		"Language": "English",
		"Part of Service": "Theotokia",
		"Feast": "Pascha"
	}
}]);
</script>

<template>
<kCard class="mb-3">
	<span id="searchBox" class="p-input-icon-left p-mt-5 searchBoxEmpty">
		<i class="pi pi-search" />
		<kInput type="text" id="searchScores" v-model="searchQuery" placeholder="Search" autofocus />
	</span>
	<Grid id="results" :grid="results" class="searchResultsEmpty"></Grid>
	<div id="empty">No scores found, try a different search or <RouterLink to="/upload">upload</RouterLink> a new score.</div>
</kCard>
</template>

<style scoped lang="scss">
#searchBox {
	transition: all 0.33s ease-in-out;
}
.searchBoxQuery {
	margin-top: 3rem !important;
}
.searchBoxEmpty {
	margin-top: 15rem !important;
}
.searchResultsEmpty {
	margin-top: 5rem !important;
	display: none;
}
.searchResultsShow {
	margin-top: 2rem !important;
	display: grid;
}
#searchScores {
	text-align: center;
}
#results {
	width: 100%;
	transition: all 0.5s ease-in-out;
}
#empty {
	display: none;
	margin-top: 5rem;
	width: 100%;
	text-align: center;
}
.display {
	display: block !important;
}
</style>
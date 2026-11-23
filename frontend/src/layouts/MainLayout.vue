<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar >
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title> Kliros Manager </q-toolbar-title>

        <div>v0.0.1</div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" bordered>
      <q-list>
        <q-item-label header> Main Menu </q-item-label>

        <EssentialLink
          v-for="link in linksList"
          :key="link.label"
          v-bind="link"
        />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { setCssVar, getCssVar, useQuasar } from "quasar";
import EssentialLink, {
  type EssentialLinkProps
} from "@/components/EssentialLink.vue";
import { getLentRange, isDateInRange, getPaschaltideRange, getPentecostRange, getPalmSundayRange, dateStripYear, colors } from "@/helpers/helpers";

const $q = useQuasar();

onMounted(() => {
  const todayDate: Date = new Date();
  let currYear = todayDate.getFullYear();

  // Feasts in Red
  if (
    isDateInRange(todayDate, {start: `11/15/${currYear}`, end: `12/24/${currYear}`}) || // Nativity Fast
    isDateInRange(todayDate, {start: `12/25/${currYear}`, end: `01/14/${currYear+1}`}) || // Nativity (usually white, but not a great color for the screen)
    isDateInRange(todayDate, getPaschaltideRange(currYear)) // Paschaltide is also white, but red is a better color for the screen
  )
    setCssVar("primary", colors.red);
  // Feasts in Blue
  else if (isDateInRange(todayDate, {start: `08/01/${currYear}`, end: `08/15/${currYear}`})) // Dormition Fast
    setCssVar("primary", colors.blue);
  // Feasts in Purple
  else if (isDateInRange(todayDate, getLentRange(currYear))) // Lent
    setCssVar("primary", colors.purple);
  // Feasts in Green
  else if (
    isDateInRange(todayDate, getPentecostRange(currYear)) || // Pentecost
    isDateInRange(todayDate, getPalmSundayRange(currYear)) // Palm Sunday
  )
    setCssVar("primary", colors.green);
  // Feasts in Gold
  else
    setCssVar("primary", colors.gold);
});

const linksList: EssentialLinkProps[] = [
  {
    label: "Home",
    caption: "Home page",
    icon: "home",
    link: "/"
  },{
    label: "Library",
    caption: "Full collection of scores",
    icon: "library_music",
    link: "/library"
  },
  {
    label: "Import",
    caption: "Upload a new score",
    icon: "upload",
    link: "/import"
  }
];

let screenSize = $q.screen.width;
const leftDrawerOpen = ref(screenSize > 1444);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>

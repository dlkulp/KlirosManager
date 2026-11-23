<template>
  <q-page v-if="user">
    <div class="center-stripe">
      <section class="lighten q-pa-md">
        <q-card class="row items-center justify-between no-wrap q-pa-md">
          <div class="row justify-start items-center">
            <q-avatar text-color="white" color="primary" rounded size="6rem">
            {{ user.initials }}
            </q-avatar>
            <span left class="text-center q-pa-sm q-ml-xl text-capitalize text-caption">
              <h4>{{ user.user.Name }}</h4>
              <!-- <span class="text-body2 text-weight-thin">{{ user.user.Email }}</span> -->
              <span class="text-body2 text-weight-thin">Joined: {{ new Date(user.user.JoinedAt).toLocaleDateString() }}</span>
            </span>
          </div>
          <span class="row">
            <div class="q-ma-sm q-pa-xs column items-center justify-start">
              <span><span v-if="store.isLoggedIn">Your </span>Uploads</span>
              <span class="text-caption">{{ user.uploads.length }}</span>
            </div>
            <div v-if="store.isLoggedIn" class="q-ma-sm q-pa-xs column items-center justify-start">
              <span>Starred</span>
              <span class="text-caption">{{ favoriteCount }}</span>
            </div>
            <div v-if="store.isLoggedIn" class="q-ma-sm q-pa-xs column items-center justify-start">
              <span>Collections</span>
              <span class="text-caption">{{ collectionCount }}</span>
            </div>
          </span>
        </q-card>
      </section>
      <template v-if="store.isLoggedIn">
        <h6 class="q-ml-lg">Favorites:</h6>
        <ScoreGrid :score-arr="(user as ProfileResponseDto).favorites"></ScoreGrid>
      </template>
      <h6 class="q-ml-lg">Uploads:</h6>
        <ScoreGrid :score-arr="user.uploads"></ScoreGrid>
    </div>
  </q-page>
</template>

<style lang="scss">
h4 {
  margin: 0px;
}
</style>

<script setup lang="ts">
import ScoreGrid, {
  type ScoreGridProps
} from "@/components/ScoreGrid.vue";
import { KlirosApi, ProfileResponseDto, PublicProfileResponseDto } from "@/types/api-client";
import { computed, onMounted, ref } from "vue";
import { store } from "@/helpers/store";

const { userId } = defineProps<{
  userId: string;
}>();
const user = ref<ProfileResponseDto | PublicProfileResponseDto>();
const api = new KlirosApi();
const collectionCount = computed(() => {
  let profile = user.value;
  return profile && "collections" in profile ? profile.collections.length : undefined;
});
const favoriteCount = computed(() => {
  let profile = user.value;
  return profile && "favorites" in profile ? profile.favorites.length : undefined;
});



onMounted(async() => {
  if (store.user) {
    user.value = store.user;
  }
  else
    try {
      user.value = await api.getProfile(Number(userId));
    }
    catch (error) {
      console.error(error);
    }
});
</script>

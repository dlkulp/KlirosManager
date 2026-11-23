import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("@/layouts/MainLayout.vue"),
    children: [
      { path: "", component: () => import("@/pages/IndexPage.vue") },
      { path: "library", component: () => import("@/pages/LibraryPage.vue") },
      { path: "library/:scoreId", component: () => import("@/pages/DetailsPage.vue"), props: true },
      { path: "profile/:userId", component: () => import("@/pages/ProfilePage.vue"), props: true }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: "/:catchAll(.*)*",
    component: () => import("@/pages/ErrorNotFound.vue")
  }
];

export default routes;

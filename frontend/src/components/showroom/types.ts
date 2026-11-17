import type { ProductLite } from "@/lib/product-lite";

/** One wall of the virtual salon: a category and the pieces hung on it. */
export type ShowroomWall = { path: string; label: string; products: ProductLite[] };

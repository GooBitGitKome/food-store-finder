"use client";

import { useState, useMemo } from "react";
import { Store } from "../types/store";
import {
  Download,
  Mail,
  Phone,
  ExternalLink,
  Filter,
  Search,
  Globe,
  Share2,
  MapPin,
  UtensilsCrossed,
  Coffee,
  ShoppingBag,
  Layers,
  Trash2,
  RotateCcw,
  Landmark,
} from "lucide-react";

interface StoreTableProps {
  stores: Store[];
  isLoading: boolean;
  onExportCsv: (filteredStores?: Store[]) => void;
}

export type StoreGenre = "all" | "restaurant" | "cafe" | "food" | "public_building";

export function getStoreGenre(store: Store): "restaurant" | "cafe" | "food" | "public_building" {
  if (
    store.genre === "public_building" ||
    store.genre === "cafe" ||
    store.genre === "food" ||
    store.genre === "restaurant"
  ) {
    return store.genre;
  }
  const cat = (store.category || "").toLowerCase();
  if (
    cat.includes("public_building") ||
    cat.includes("公共施設") ||
    cat.includes("公的") ||
    cat.includes("役所") ||
    cat.includes("公民館")
  ) {
    return "public_building";
  }
  if (
    cat.includes("カフェ") ||
    cat.includes("喫茶") ||
    cat.includes("バー") ||
    cat.includes("パブ") ||
    cat.includes("cafe") ||
    cat.includes("bar") ||
    cat.includes("pub")
  ) {
    return "cafe";
  }
  if (
    cat.includes("パン") ||
    cat.includes("ベーカリー") ||
    cat.includes("菓子") ||
    cat.includes("スイーツ") ||
    cat.includes("肉") ||
    cat.includes("魚") ||
    cat.includes("惣菜") ||
    cat.includes("食品") ||
    cat.includes("bakery") ||
    cat.includes("confectionery") ||
    cat.includes("deli") ||
    cat.includes("shop")
  ) {
    return "food";
  }
  return "restaurant";
}

export function getGoogleMapsUrl(store: Store): string {
  if (store.google_maps_url) return store.google_maps_url;
  const target = `${store.name} ${store.address || ""}`.trim();
  if (target && target !== "名称未設定") {
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(target)}`;
  }
  return `https://www.google.com/maps/search/?api=1&query=${store.lat},${store.lon}`;
}

export default function StoreTable({ stores, isLoading, onExportCsv }: StoreTableProps) {
  const [filterText, setFilterText] = useState("");
  const [selectedGenre, setSelectedGenre] = useState<StoreGenre>("all");
  const [onlyWithEmail, setOnlyWithEmail] = useState(false);
  const [onlyWithPhone, setOnlyWithPhone] = useState(false);
  const [excludedIds, setExcludedIds] = useState<Set<string>>(new Set());

  // 店舗のワンクリック除外
  const handleExcludeStore = (id: string) => {
    setExcludedIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  };

  // 除外店舗の全復元
  const handleResetExcluded = () => {
    setExcludedIds(new Set());
  };

  // ジャンル別件数の集計 (除外されていない店舗対象)
  const genreCounts = useMemo(() => {
    const validStores = stores.filter((s) => !excludedIds.has(s.id));
    const counts = { all: validStores.length, restaurant: 0, cafe: 0, food: 0, public_building: 0 };
    for (const s of validStores) {
      const g = getStoreGenre(s);
      counts[g] = (counts[g] || 0) + 1;
    }
    return counts;
  }, [stores, excludedIds]);

  const filteredStores = useMemo(() => {
    return stores.filter((s) => {
      // ユーザーが除外した店舗をスキップ
      if (excludedIds.has(s.id)) return false;

      // ジャンルフィルタ
      if (selectedGenre !== "all") {
        const g = getStoreGenre(s);
        if (g !== selectedGenre) return false;
      }
      // テキスト検索フィルタ
      if (filterText) {
        const query = filterText.toLowerCase();
        const matchesName = s.name.toLowerCase().includes(query);
        const matchesCat = s.category.toLowerCase().includes(query);
        const matchesAddr = s.address.toLowerCase().includes(query);
        if (!matchesName && !matchesCat && !matchesAddr) return false;
      }
      // 連絡先フィルタ
      if (onlyWithEmail && !s.email) return false;
      if (onlyWithPhone && !s.phone) return false;
      return true;
    });
  }, [stores, excludedIds, selectedGenre, filterText, onlyWithEmail, onlyWithPhone]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full overflow-hidden">
      {/* ツールバー */}
      <div className="p-3 sm:p-4 border-b border-slate-100 flex flex-col gap-3 bg-slate-50/70">
        {/* 上段: ジャンル分類タブボタン */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-500 font-semibold mr-1 flex items-center gap-1 whitespace-nowrap">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            ジャンル分類:
          </span>
          <button
            type="button"
            onClick={() => setSelectedGenre("all")}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
              selectedGenre === "all"
                ? "bg-blue-600 text-white shadow-xs font-semibold"
                : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            <span>すべて</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedGenre === "all" ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {genreCounts.all}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedGenre("restaurant")}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
              selectedGenre === "restaurant"
                ? "bg-amber-600 text-white shadow-xs font-semibold"
                : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            <UtensilsCrossed className="w-3.5 h-3.5" />
            <span>飲食店・レストラン</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedGenre === "restaurant" ? "bg-amber-700 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {genreCounts.restaurant}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedGenre("cafe")}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
              selectedGenre === "cafe"
                ? "bg-rose-600 text-white shadow-xs font-semibold"
                : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            <Coffee className="w-3.5 h-3.5" />
            <span>カフェ・喫茶・バー</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedGenre === "cafe" ? "bg-rose-700 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {genreCounts.cafe}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedGenre("food")}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
              selectedGenre === "food"
                ? "bg-emerald-600 text-white shadow-xs font-semibold"
                : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <span>食品・ベーカリー・専門店</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedGenre === "food" ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {genreCounts.food}
            </span>
          </button>

          {genreCounts.public_building > 0 && (
            <button
              type="button"
              onClick={() => setSelectedGenre("public_building")}
              className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
                selectedGenre === "public_building"
                  ? "bg-slate-700 text-white shadow-xs font-semibold"
                  : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
              }`}
            >
              <Landmark className="w-3.5 h-3.5" />
              <span>公共施設 (検出)</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  selectedGenre === "public_building"
                    ? "bg-slate-800 text-white"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {genreCounts.public_building}
              </span>
            </button>
          )}
        </div>

        {/* 下段: テキスト検索 & 各種オプション & CSVエクスポート */}
        <div className="flex flex-col sm:flex-row gap-2.5 items-center justify-between">
          <div className="flex items-center gap-2 w-full sm:w-auto flex-1 max-w-sm">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="店名・カテゴリ・住所で絞り込み..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end flex-wrap">
            <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer bg-white px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition">
              <input
                type="checkbox"
                checked={onlyWithEmail}
                onChange={(e) => setOnlyWithEmail(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 h-3.5 w-3.5"
              />
              <span>メールありのみ</span>
            </label>

            <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer bg-white px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition">
              <input
                type="checkbox"
                checked={onlyWithPhone}
                onChange={(e) => setOnlyWithPhone(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 h-3.5 w-3.5"
              />
              <span>電話ありのみ</span>
            </label>

            {excludedIds.size > 0 && (
              <button
                type="button"
                onClick={handleResetExcluded}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold rounded-lg border border-amber-200 transition"
                title="除外した店舗をすべて元に戻す"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
                <span>除外 {excludedIds.size}件を復元</span>
              </button>
            )}

            <button
              onClick={() => onExportCsv(filteredStores)}
              disabled={filteredStores.length === 0 || isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white text-xs font-semibold rounded-lg shadow-sm transition"
              title="現在の一覧 (絞り込み・除外反映済み) をCSVダウンロード"
            >
              <Download className="w-3.5 h-3.5" />
              CSV保存 ({filteredStores.length}件)
            </button>
          </div>
        </div>
      </div>

      {/* テーブル本体 */}
      <div className="flex-1 overflow-auto max-h-[500px]">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent mb-3"></div>
            <p className="text-sm font-medium">Overpass APIから店舗情報を抽出・判定中...</p>
          </div>
        ) : filteredStores.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Filter className="w-10 h-10 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">該当する店舗が見つかりませんでした。</p>
            <p className="text-xs text-slate-400 mt-1">検索半径を広げるか、中心地点を変更してください。</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold sticky top-0 border-b border-slate-200 z-10">
              <tr>
                <th className="py-2.5 px-3">店舗情報 / ジャンル</th>
                <th className="py-2.5 px-3 whitespace-nowrap">Google Map誘導</th>
                <th className="py-2.5 px-3">住所 / 所在地</th>
                <th className="py-2.5 px-3 whitespace-nowrap">HP判定</th>
                <th className="py-2.5 px-3">E-mail連絡先</th>
                <th className="py-2.5 px-3">電話 / SNS / ポータル</th>
                <th className="py-2.5 px-3 whitespace-nowrap text-right">除外</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStores.map((store) => {
                const genre = getStoreGenre(store);
                const gmapsUrl = getGoogleMapsUrl(store);

                return (
                  <tr key={store.id} className="hover:bg-blue-50/40 transition">
                    {/* 店舗名 & 業態 & ジャンル */}
                    <td className="py-3 px-3">
                      <div className="flex flex-col gap-1">
                        <a
                          href={gmapsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-bold text-slate-900 text-sm hover:text-blue-600 hover:underline inline-flex items-center gap-1 group"
                          title="Googleマップで店舗を開く"
                        >
                          <span>{store.name}</span>
                          <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-600 transition flex-shrink-0" />
                        </a>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {genre === "cafe" ? (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
                              <Coffee className="w-2.5 h-2.5" />
                              <span>{store.category}</span>
                            </span>
                          ) : genre === "food" ? (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <ShoppingBag className="w-2.5 h-2.5" />
                              <span>{store.category}</span>
                            </span>
                          ) : genre === "public_building" ? (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-300">
                              <Landmark className="w-2.5 h-2.5 text-slate-600" />
                              <span>{store.category}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
                              <UtensilsCrossed className="w-2.5 h-2.5" />
                              <span>{store.category}</span>
                            </span>
                          )}
                          {store.id?.startsWith("overture_") || store.data_source === "overture" ? (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                              Overture
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-slate-50 text-slate-500 border border-slate-200">
                              OSM
                            </span>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Google Map 誘導ボタン */}
                    <td className="py-3 px-3 whitespace-nowrap">
                      <a
                        href={gmapsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition shadow-xs group"
                        title={`${store.name} のGoogleマップ(別ページ)を開く`}
                      >
                        <MapPin className="w-3.5 h-3.5 text-red-600 group-hover:scale-110 transition flex-shrink-0" />
                        <span>Google Map ↗</span>
                      </a>
                    </td>

                    {/* 住所 */}
                    <td className="py-3 px-3 max-w-[180px]">
                      <div className="text-slate-700 truncate" title={store.address || "住所詳細なし"}>
                        {store.address || <span className="text-slate-400 italic">番地情報なし</span>}
                      </div>
                    </td>

                  {/* HP判定 */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    {store.has_own_website ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-100 text-blue-700">
                        <Globe className="w-3 h-3" /> 自社HPあり
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-800">
                        ● 自社HPなし
                      </span>
                    )}
                  </td>

                  {/* E-mail */}
                  <td className="py-3 px-3">
                    {store.email ? (
                      <div className="flex flex-col gap-0.5">
                        <a
                          href={`mailto:${store.email}`}
                          className="inline-flex items-center gap-1 text-emerald-700 font-medium hover:underline"
                        >
                          <Mail className="w-3 h-3" />
                          <span>{store.email}</span>
                        </a>
                        {store.email_source_url && (
                          <a
                            href={store.email_source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-slate-400 flex items-center gap-0.5 hover:text-slate-600 truncate max-w-[160px]"
                            title={store.email_source_url}
                          >
                            <ExternalLink className="w-2.5 h-2.5" />
                            <span>取得元リンク</span>
                          </a>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400 italic">未検出 (代替情報で補完)</span>
                    )}
                  </td>

                  {/* 電話 / SNS / ポータル */}
                  <td className="py-3 px-3">
                    <div className="flex flex-col gap-1">
                      {store.phone ? (
                        <a
                          href={`tel:${store.phone}`}
                          className="inline-flex items-center gap-1 text-slate-700 hover:text-blue-600"
                        >
                          <Phone className="w-3 h-3 text-slate-400" />
                          <span>{store.phone}</span>
                        </a>
                      ) : null}

                      {store.sns_urls.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          {store.sns_urls.map((url, i) => (
                            <a
                              key={i}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-pink-50 text-pink-700 text-[10px] hover:bg-pink-100"
                            >
                              <Share2 className="w-2.5 h-2.5" /> SNS
                            </a>
                          ))}
                        </div>
                      )}

                      {store.portal_urls.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          {store.portal_urls.slice(0, 2).map((url, i) => (
                            <a
                              key={i}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] hover:bg-slate-200"
                            >
                              <ExternalLink className="w-2.5 h-2.5" /> ポータル
                            </a>
                          ))}
                        </div>
                      )}

                      {!store.phone && store.sns_urls.length === 0 && store.portal_urls.length === 0 && (
                        <span className="text-slate-400 text-[10px]">-</span>
                      )}
                    </div>
                  </td>

                  {/* 除外ボタン */}
                  <td className="py-3 px-3 whitespace-nowrap text-right">
                    <button
                      type="button"
                      onClick={() => handleExcludeStore(store.id)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg border border-slate-200 hover:border-red-200 transition"
                      title="Googleマップで公式HPを確認したため一覧から除外"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>除外</span>
                    </button>
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

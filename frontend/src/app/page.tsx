"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Store, SearchResponse } from "../types/store";
import StoreTable from "../components/StoreTable";
import { Search, MapPin, Sliders, Database, Building2, MailCheck, AlertCircle, Crosshair, Globe, Sparkles } from "lucide-react";

// Leafletマップはブラウザ環境(window)が必要なためSSRを無効化
const MapComponent = dynamic(() => import("../components/MapComponent"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[450px] lg:h-[540px] rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 text-sm">
      地図コンポーネントを読み込み中...
    </div>
  ),
});

const rawApiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const API_BASE = rawApiBase.replace(/\/+$/, "");

export default function Home() {
  const [addressInput, setAddressInput] = useState("東京都港区麻布十番");
  const [currentLocationName, setCurrentLocationName] = useState("東京都港区麻布十番");
  const [center, setCenter] = useState<[number, number]>([35.65655, 139.73617]); // 麻布十番初期値
  const [radius, setRadius] = useState<number>(500); // 500m
  const [categories, setCategories] = useState<string[]>(["restaurant", "cafe", "food"]);
  const [onlyWithoutWebsite, setOnlyWithoutWebsite] = useState<boolean>(true);
  const [enrichContacts, setEnrichContacts] = useState<boolean>(true);
  const [dataSource, setDataSource] = useState<"overture" | "osm">("overture");

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [stores, setStores] = useState<Store[]>([]);

  // 地名からジオコーディング
  const handleGeocode = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!addressInput.trim()) return;

    setErrorMsg(null);
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/stores/geocode?query=${encodeURIComponent(addressInput)}`);
      if (!res.ok) {
        throw new Error("指定された住所・地名の座標を特定できませんでした。");
      }
      const data = await res.json();
      setCenter([data.lat, data.lon]);
      setCurrentLocationName(data.display_name);
      
      // 自動的に検索も実行
      await executeSearch(data.lat, data.lon);
    } catch (err: any) {
      setErrorMsg(err.message || "エラーが発生しました");
      setIsLoading(false);
    }
  };

  const [isLocating, setIsLocating] = useState<boolean>(false);

  // 現在地取得 (Geolocation API)
  const handleGetCurrentLocation = () => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      setErrorMsg("お使いのブラウザは現在地取得（Geolocation API）に対応していません。");
      return;
    }
    setIsLocating(true);
    setErrorMsg(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        setCenter([lat, lon]);
        const locLabel = `現在地 (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
        setCurrentLocationName(locLabel);
        setAddressInput(locLabel);
        setIsLocating(false);
      },
      (err) => {
        setIsLocating(false);
        if (err.code === 1) {
          setErrorMsg("位置情報の利用が拒否されました。ブラウザの設定で位置情報の利用を許可してください。");
        } else if (err.code === 2) {
          setErrorMsg("現在地を特定できませんでした。通信環境をご確認ください。");
        } else if (err.code === 3) {
          setErrorMsg("現在地取得がタイムアウトしました。");
        } else {
          setErrorMsg(`現在地の取得に失敗しました: ${err.message}`);
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  };

  // ピン移動時
  const handlePinChange = (lat: number, lon: number) => {
    setCenter([lat, lon]);
    setCurrentLocationName(`Pin指定座標: (${lat.toFixed(5)}, ${lon.toFixed(5)})`);
  };

  // 検索API実行
  const executeSearch = async (lat = center[0], lon = center[1]) => {
    setErrorMsg(null);
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/stores/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat,
          lon,
          radius_meters: radius,
          categories,
          only_without_website: onlyWithoutWebsite,
          enrich_contacts: enrichContacts,
          data_source: dataSource,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "店舗データの取得に失敗しました。");
      }

      const data: SearchResponse = await res.json();
      setSearchResponse(data);
      setStores(data.stores);
    } catch (err: any) {
      setErrorMsg(err.message || "検索中にエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  };

  // CSVエクスポート (絞り込み・除外後の店舗リストを反映可能)
  const handleExportCsv = async (exportStores?: Store[]) => {
    const targetStores = exportStores || stores;
    if (targetStores.length === 0) return;
    try {
      const res = await fetch(`${API_BASE}/stores/export-csv`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(targetStores),
      });

      if (!res.ok) throw new Error("CSVの生成に失敗しました。");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `food_stores_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert("CSVダウンロードエラー: " + err.message);
    }
  };

  return (
    <main className="min-h-screen p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto flex flex-col gap-6">
      {/* ヘッダー */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="w-7 h-7 text-blue-600" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Food Store Finder
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-blue-100 text-blue-800 inline-flex items-center gap-1">
              {dataSource === "overture" ? (
                <>
                  <Globe className="w-3 h-3 text-blue-600" />
                  <span>Overture Maps</span>
                </>
              ) : (
                <span>🗺️ OpenStreetMap</span>
              )}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            自社Webサイトを持たない飲食店・食品店を発見し、メールおよび代替連絡先（電話・SNS等）を一覧化。Googleマップでの別タブ確認やFood・カフェ等のジャンル分類フィルタに対応
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => executeSearch()}
            disabled={isLoading}
            className="flex items-center justify-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white text-sm font-bold rounded-lg shadow transition whitespace-nowrap min-w-fit flex-shrink-0"
          >
            {isLoading ? (
              <span className="inline-block animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full flex-shrink-0" />
            ) : (
              <Search className="w-4 h-4 flex-shrink-0" />
            )}
            <span className="whitespace-nowrap">この条件で検索実行</span>
          </button>
        </div>
      </header>

      {/* エラーメッセージ */}
      {errorMsg && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 検索コントロールバー */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        {/* 1. 地名・住所指定 */}
        <form onSubmit={handleGeocode} className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-blue-600" />
            <span>エリア・住所検索 (Pin中心位置)</span>
          </label>
          <div className="flex gap-1.5">
            <input
              type="text"
              value={addressInput}
              onChange={(e) => setAddressInput(e.target.value)}
              placeholder="例: 東京都港区麻布十番, 渋谷区神南"
              className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-medium rounded-lg transition"
            >
              特定
            </button>
            <button
              type="button"
              onClick={handleGetCurrentLocation}
              disabled={isLocating}
              title="端末の現在地(GPS)を取得"
              className="px-3 py-2 bg-blue-50 hover:bg-blue-100 disabled:bg-slate-100 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200 transition flex items-center gap-1 whitespace-nowrap"
            >
              <Crosshair className={`w-3.5 h-3.5 ${isLocating ? "animate-spin text-blue-600" : ""}`} />
              <span>{isLocating ? "取得中..." : "現在地"}</span>
            </button>
          </div>
          <p className="text-[11px] text-slate-400 truncate" title={currentLocationName}>
            現在中心: {currentLocationName}
          </p>
        </form>

        {/* 2. 半径指定 (100m 〜 100km) */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <Sliders className="w-3.5 h-3.5 text-blue-600" />
              <span>探索半径 (Pinからの範囲: 最大100km)</span>
            </label>
            <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
              {radius >= 1000 ? `${(radius / 1000).toLocaleString()} km` : `${radius} m`}
            </span>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <input
              type="range"
              min={100}
              max={100000}
              step={radius >= 20000 ? 5000 : (radius >= 5000 ? 1000 : 200)}
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>
          <div className="flex gap-1 mt-0.5 flex-wrap">
            {[500, 1000, 5000, 10000, 30000, 50000, 100000].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRadius(r)}
                className={`text-[10px] px-2 py-0.5 rounded border transition ${
                  radius === r
                    ? "bg-blue-600 border-blue-600 text-white font-bold shadow-xs"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {r >= 1000 ? `${r / 1000}km` : `${r}m`}
              </button>
            ))}
          </div>
        </div>

        {/* 3. オプションフィルタ & ジャンル指定 */}
        <div className="flex flex-col gap-2">
          {/* データソース選択トグル */}
          <div className="flex flex-col gap-1.5 pb-2 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                <Globe className="w-3.5 h-3.5 text-blue-600" />
                <span>データソース (オープンデータ)</span>
              </label>
              <span className="text-[10px] text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded font-medium border border-blue-200">
                {dataSource === "overture" ? "高精度・HP情報豊富" : "軽量・OSM"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1 p-0.5 bg-slate-100 rounded-lg">
              <button
                type="button"
                onClick={() => setDataSource("overture")}
                className={`px-2 py-1.5 rounded-md text-xs font-medium transition flex items-center justify-center gap-1 ${
                  dataSource === "overture"
                    ? "bg-white text-blue-700 shadow-xs font-bold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Sparkles className="w-3 h-3 text-amber-500" />
                <span>Overture Maps</span>
              </button>
              <button
                type="button"
                onClick={() => setDataSource("osm")}
                className={`px-2 py-1.5 rounded-md text-xs font-medium transition flex items-center justify-center gap-1 ${
                  dataSource === "osm"
                    ? "bg-white text-blue-700 shadow-xs font-bold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <span>🗺️ OpenStreetMap</span>
              </button>
            </div>
          </div>

          <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span>抽出条件・ジャンル選択</span>
          </label>
          <div className="flex flex-col gap-1.5 text-xs text-slate-700">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={onlyWithoutWebsite}
                onChange={(e) => setOnlyWithoutWebsite(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">自前HPを持たない店舗のみ抽出</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={enrichContacts}
                onChange={(e) => setEnrichContacts(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span>連絡先ハイブリッド探索 (メール/SNS発掘)</span>
            </label>
          </div>

          {/* ジャンル選択チェックボックス */}
          <div className="pt-2 border-t border-slate-100 flex flex-col gap-1">
            <span className="text-[11px] font-semibold text-slate-600">検索対象ジャンル:</span>
            <div className="flex items-center gap-2 flex-wrap text-xs">
              <label className="flex items-center gap-1 cursor-pointer bg-slate-50 px-2 py-0.5 rounded border border-slate-200 hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={categories.includes("restaurant")}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setCategories([...categories, "restaurant"]);
                    } else if (categories.length > 1) {
                      setCategories(categories.filter((c) => c !== "restaurant"));
                    }
                  }}
                  className="rounded text-amber-600 focus:ring-amber-500 h-3 w-3"
                />
                <span className="text-[11px] text-slate-700 font-medium">🍽️ 飲食店</span>
              </label>

              <label className="flex items-center gap-1 cursor-pointer bg-slate-50 px-2 py-0.5 rounded border border-slate-200 hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={categories.includes("cafe")}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setCategories([...categories, "cafe"]);
                    } else if (categories.length > 1) {
                      setCategories(categories.filter((c) => c !== "cafe"));
                    }
                  }}
                  className="rounded text-rose-600 focus:ring-rose-500 h-3 w-3"
                />
                <span className="text-[11px] text-slate-700 font-medium">☕ カフェ</span>
              </label>

              <label className="flex items-center gap-1 cursor-pointer bg-slate-50 px-2 py-0.5 rounded border border-slate-200 hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={categories.includes("food")}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setCategories([...categories, "food"]);
                    } else if (categories.length > 1) {
                      setCategories(categories.filter((c) => c !== "food"));
                    }
                  }}
                  className="rounded text-emerald-600 focus:ring-emerald-500 h-3 w-3"
                />
                <span className="text-[11px] text-slate-700 font-medium">🥖 食品・ベーカリー</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* サマリーカード */}
      {searchResponse && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="font-semibold text-slate-800">検索結果サマリー</span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-medium text-[11px] bg-blue-50 text-blue-700 border border-blue-200">
                {searchResponse.data_source?.includes("overture") ? (
                  <>
                    <Globe className="w-3 h-3 text-blue-600" />
                    <span>データソース: Overture Maps Places</span>
                  </>
                ) : (
                  <span>データソース: OpenStreetMap</span>
                )}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">範囲内 総店舗数</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{searchResponse.total_found} 件</p>
            </div>
            <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600">
              <Building2 className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-amber-600">自社HPなし 店舗数</p>
              <p className="text-2xl font-bold text-amber-700 mt-1">{searchResponse.without_website_count} 件</p>
            </div>
            <div className="p-2.5 bg-amber-50 rounded-xl text-amber-600">
              <span className="text-sm font-bold">HP無</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-emerald-600">連絡先保有 (TEL/SNS/Mail)</p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{searchResponse.with_contact_count} 件</p>
            </div>
            <div className="p-2.5 bg-emerald-50 rounded-xl text-emerald-600">
              <MailCheck className="w-5 h-5" />
            </div>
          </div>
          </div>
        </div>
      )}

      {/* メインコンテンツ: 地図 ＋ テーブル */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* 左側: インタラクティブマップ */}
        <div className="lg:col-span-5 flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>地図上のクリックまたはPinドラッグで中心を変更できます</span>
          </div>
          <MapComponent
            center={center}
            radius={radius}
            stores={stores}
            onPinChange={handlePinChange}
          />
        </div>

        {/* 右側: 店舗一覧テーブル & CSVエクスポート */}
        <div className="lg:col-span-7 h-full">
          <StoreTable
            stores={stores}
            isLoading={isLoading}
            onExportCsv={handleExportCsv}
          />
        </div>
      </div>
    </main>
  );
}

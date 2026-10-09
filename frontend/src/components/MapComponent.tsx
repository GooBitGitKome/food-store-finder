"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { Store } from "../types/store";

interface MapProps {
  center: [number, number];
  radius: number;
  stores: Store[];
  onPinChange: (lat: number, lon: number) => void;
}

export default function MapComponent({ center, radius, stores, onPinChange }: MapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const centerMarkerRef = useRef<L.Marker | null>(null);
  const circleRef = useRef<L.Circle | null>(null);
  const storeLayerRef = useRef<L.LayerGroup | null>(null);

  // 初回マップ初期化
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // デフォルトマーカーアイコンの修正
    const customCenterIcon = L.divIcon({
      className: "custom-center-pin",
      html: `
        <div style="background-color: #ef4444; width: 26px; height: 26px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
          <div style="width: 8px; height: 8px; background: white; border-radius: 50%; transform: rotate(45deg);"></div>
        </div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 26],
    });

    const map = L.map(mapContainerRef.current).setView(center, 15);
    mapInstanceRef.current = map;

    // OpenStreetMap タイルレイヤー
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // 半径サークル
    const circle = L.circle(center, {
      radius: radius,
      color: "#3b82f6",
      fillColor: "#60a5fa",
      fillOpacity: 0.18,
      weight: 2,
    }).addTo(map);
    circleRef.current = circle;

    // ドラッグ可能な中心ピン
    const marker = L.marker(center, {
      draggable: true,
      icon: customCenterIcon,
    }).addTo(map);
    centerMarkerRef.current = marker;

    marker.on("dragend", () => {
      const pos = marker.getLatLng();
      onPinChange(pos.lat, pos.lng);
    });

    // 地図クリックで中心ピン移動
    map.on("click", (e: L.LeafletMouseEvent) => {
      marker.setLatLng(e.latlng);
      circle.setLatLng(e.latlng);
      onPinChange(e.latlng.lat, e.latlng.lng);
    });

    // 店舗マーカー用レイヤーグループ
    const storeLayer = L.layerGroup().addTo(map);
    storeLayerRef.current = storeLayer;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 中心座標と半径の同期
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    if (centerMarkerRef.current) {
      centerMarkerRef.current.setLatLng(center);
    }
    if (circleRef.current) {
      circleRef.current.setLatLng(center);
      circleRef.current.setRadius(radius);
      map.fitBounds(circleRef.current.getBounds(), { padding: [30, 30], maxZoom: 16 });
    } else {
      map.panTo(center);
    }
  }, [center, radius]);

  // 店舗マーカーの描画
  useEffect(() => {
    if (!storeLayerRef.current || !mapInstanceRef.current) return;
    const storeLayer = storeLayerRef.current;
    storeLayer.clearLayers();

    const storeIconWithMail = L.divIcon({
      className: "store-pin-mail",
      html: `
        <div style="background-color: #10b981; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
      `,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });

    const storeIconDefault = L.divIcon({
      className: "store-pin-default",
      html: `
        <div style="background-color: #6366f1; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
      `,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    stores.forEach((store) => {
      const hasMail = Boolean(store.email);
      const marker = L.marker([store.lat, store.lon], {
        icon: hasMail ? storeIconWithMail : storeIconDefault,
      });

      const gmapsTarget = `${store.name} ${store.address || ""}`.trim();
      const gmapsUrl =
        store.google_maps_url ||
        (gmapsTarget && store.name !== "名称未設定"
          ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(gmapsTarget)}`
          : `https://www.google.com/maps/search/?api=1&query=${store.lat},${store.lon}`);

      const popupHtml = `
        <div class="p-1 min-w-[210px] text-xs">
          <p class="font-bold text-sm text-slate-800">${store.name}</p>
          <p class="text-slate-500 mb-1">${store.category}</p>
          ${store.phone ? `<p class="text-slate-600">TEL: ${store.phone}</p>` : ""}
          <p class="mt-1 font-semibold ${store.has_own_website ? "text-blue-600" : "text-amber-600"}">
            ${store.has_own_website ? "✓ 自社HPあり" : "● 自社HPなし"}
          </p>
          ${
            store.email
              ? `<p class="mt-1 text-emerald-600 font-bold bg-emerald-50 p-1 rounded">✉ ${store.email}</p>`
              : '<p class="mt-1 text-slate-400">メール: 未登録/探索中</p>'
          }
          <div class="mt-2.5 pt-2 border-t border-slate-200">
            <a
              href="${gmapsUrl}"
              target="_blank"
              rel="noopener noreferrer"
              style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600; color: #b91c1c; background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; text-decoration: none;"
            >
              📍 Googleマップで開く ↗
            </a>
          </div>
        </div>
      `;
      marker.bindPopup(popupHtml);
      storeLayer.addLayer(marker);
    });
  }, [stores]);

  return (
    <div className="relative w-full h-[450px] lg:h-[580px] xl:h-[680px] rounded-xl overflow-hidden border border-slate-200 shadow-inner">
      <div ref={mapContainerRef} className="w-full h-full" />
      <div className="absolute bottom-3 left-3 z-[1000] bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 shadow border border-slate-200 flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> 検索Pin
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> メールあり
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block"></span> HPなし店舗
        </span>
      </div>
    </div>
  );
}

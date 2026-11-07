import React, { useState, useEffect } from "react";
import { Search, X, Image as ImageIcon, Film, Upload, Check, Loader2, Sparkles, RefreshCw } from "lucide-react";
import { api, StockSearchItem } from "@/lib/api";
import { cn } from "@/lib/utils";

interface StockPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  sceneIdx: number;
  initialQuery?: string;
  keywords?: string[];
  workerId?: string;
  onSelectAsset: (assetPathOrUrl: string, assetName: string) => void;
}

export function StockPickerModal({
  isOpen,
  onClose,
  sceneIdx,
  initialQuery = "",
  keywords = [],
  workerId = "tech",
  onSelectAsset,
}: StockPickerModalProps) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<StockSearchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAssetUrl, setSelectedAssetUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      const q = initialQuery || (keywords.length > 0 ? keywords[0].replace("#", "") : "modern technology");
      setQuery(q);
      performSearch(q);
    }
  }, [isOpen, initialQuery]);

  const performSearch = async (searchTerm: string) => {
    const clean = searchTerm.trim().replace("#", "");
    if (!clean) return;
    setIsLoading(true);
    setUploadError(null);
    try {
      const items = await api.searchStock(clean, "portrait");
      setResults(items);
    } catch (err: any) {
      console.warn("Stock search error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const uploaded = await api.uploadAsset(file, workerId);
      onSelectAsset(uploaded.file_path, file.name);
      onClose();
    } catch (err: any) {
      setUploadError(err.message || "Failed uploading file");
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl rounded-2xl border border-border bg-[#0d121c] p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-hive/10 border border-hive/30 flex items-center justify-center text-hive">
              <ImageIcon size={18} />
            </div>
            <div>
              <h2 className="font-display text-base font-bold text-gray-100">
                Replace Visual Asset — Scene {sceneIdx + 1}
              </h2>
              <p className="font-mono text-[10px] text-gray-400">
                Search live 4K vertical photography from Unsplash, Vault, or upload your own media.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-surface hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search Input & Action Bar */}
        <div className="space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              performSearch(query);
            }}
            className="flex gap-2"
          >
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search photogenic 9:16 stock (e.g. quantum leap, tokyo neon, supercomputer)..."
                className="w-full rounded-xl border border-border bg-surface-deep pl-9 pr-3 py-2 text-xs text-gray-100 outline-none focus:border-hive/60 font-mono transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="flex items-center gap-1.5 rounded-xl bg-hive px-4 py-2 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400 transition-colors disabled:opacity-50"
            >
              {isLoading ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />}
              SEARCH
            </button>
          </form>

          {/* Keyword suggestion pills */}
          {keywords.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap font-mono text-[10px]">
              <span className="text-gray-500 text-[9px] uppercase">SUGGESTIONS:</span>
              {keywords.map((kw, i) => {
                const cleanKw = kw.replace("#", "").trim();
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => {
                      setQuery(cleanKw);
                      performSearch(cleanKw);
                    }}
                    className="rounded-md border border-border/70 bg-surface px-2 py-0.5 text-gray-300 hover:border-hive/50 hover:text-hive transition-colors text-[9px]"
                  >
                    #{cleanKw}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Results Gallery Grid */}
        <div className="flex-1 overflow-y-auto pr-1 min-h-[280px]">
          {isLoading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-gray-400 font-mono text-xs">
              <Loader2 size={24} className="animate-spin text-hive" />
              <span>Querying 4K stock database...</span>
            </div>
          ) : results.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {results.map((item) => {
                const isSelected = selectedAssetUrl === item.regular_url;
                return (
                  <div
                    key={item.id}
                    onClick={() => {
                      setSelectedAssetUrl(item.regular_url);
                      onSelectAsset(item.regular_url, item.title || item.id);
                      onClose();
                    }}
                    className={cn(
                      "group relative aspect-[9/16] rounded-xl overflow-hidden border cursor-pointer transition-all hover:scale-[1.02] shadow-md",
                      isSelected
                        ? "border-hive ring-2 ring-hive/60"
                        : "border-border/80 hover:border-hive/50"
                    )}
                  >
                    <img
                      src={item.thumbnail_url}
                      alt={item.title}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-80 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute bottom-2 left-2 right-2 space-y-0.5">
                      <p className="font-mono text-[9px] text-white line-clamp-1 font-semibold">{item.title}</p>
                      <p className="font-mono text-[8px] text-gray-400 truncate">
                        {item.author} • <span className="text-emerald-400 uppercase">{item.source}</span>
                      </p>
                    </div>
                    <div className="absolute top-2 right-2 rounded-full bg-black/60 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Check size={12} className="text-hive" />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-gray-500 font-mono text-xs border border-dashed border-border rounded-xl">
              <ImageIcon size={32} className="text-gray-600 mb-1" />
              <span>No direct stock matches found for "{query}".</span>
              <span className="text-[10px] text-gray-600">Try broader keywords or upload your own file below.</span>
            </div>
          )}
        </div>

        {/* Footer: Upload Custom Media */}
        <div className="border-t border-border/80 pt-3 flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 rounded-xl border border-border bg-surface px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:border-border/80 cursor-pointer transition-colors">
              {isUploading ? (
                <>
                  <Loader2 size={13} className="animate-spin text-hive" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload size={13} className="text-hive" />
                  <span>Upload Local Image/Video</span>
                </>
              )}
              <input
                type="file"
                accept="image/*,video/*"
                onChange={handleFileUpload}
                disabled={isUploading}
                className="hidden"
              />
            </label>
            {uploadError && <span className="text-[10px] text-red-400">{uploadError}</span>}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-border bg-surface px-4 py-1.5 text-xs text-gray-300 hover:text-white"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}


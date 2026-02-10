"use client";

import { useState, useRef, useEffect } from "react";
import { useDebounce } from "@/hooks/use-debounce";
import { Input } from "@/components/ui/input";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SubredditResult {
  data: {
    display_name: string;
    subscribers: number;
  };
}

interface SubredditAutocompleteProps {
  selected: string[];
  onSelect: (subreddits: string[]) => void;
  maxItems?: number;
}

export function SubredditAutocomplete({
  selected,
  onSelect,
  maxItems = 10,
}: SubredditAutocompleteProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SubredditResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch subreddits from Reddit API
  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    const fetchSubreddits = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `/api/subreddits/search?q=${encodeURIComponent(debouncedQuery)}`
        );

        if (response.ok) {
          const data = await response.json();
          setResults(data.data.children || []);
          setShowDropdown(true);
        }
      } catch (error) {
        // Silently handle errors - don't crash the UI
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubreddits();
  }, [debouncedQuery]);

  // Handle clicking outside dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSelectSubreddit = (subreddit: string) => {
    if (!selected.includes(subreddit) && selected.length < maxItems) {
      onSelect([...selected, subreddit]);
      setQuery("");
      setShowDropdown(false);
    }
  };

  const handleRemoveSubreddit = (subreddit: string) => {
    onSelect(selected.filter((s) => s !== subreddit));
  };

  const formatSubscribers = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  return (
    <div className="space-y-2" ref={dropdownRef}>
      <div className="relative">
        <Input
          type="text"
          placeholder="Search for subreddits..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setShowDropdown(true);
          }}
        />
        {showDropdown && results.length > 0 && (
          <div className="absolute z-10 mt-1 w-full rounded-md border bg-popover shadow-lg">
            <ul className="max-h-60 overflow-auto py-1">
              {results.map((result) => {
                const subreddit = result.data.display_name;
                const isSelected = selected.includes(subreddit);
                return (
                  <li
                    key={subreddit}
                    className={`cursor-pointer px-3 py-2 hover:bg-accent ${
                      isSelected ? "opacity-50" : ""
                    }`}
                    onClick={() => !isSelected && handleSelectSubreddit(subreddit)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">r/{subreddit}</span>
                      <span className="text-sm text-muted-foreground">
                        {formatSubscribers(result.data.subscribers)} members
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            Loading...
          </div>
        )}
      </div>

      {/* Selected subreddits as chips */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map((subreddit) => (
            <div
              key={subreddit}
              className="flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-sm"
            >
              <span>r/{subreddit}</span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => handleRemoveSubreddit(subreddit)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

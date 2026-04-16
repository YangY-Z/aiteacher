/**
 * 教学图片Hook
 * 用于获取和缓存教学图片
 */

import { useState, useEffect } from 'react';
import { teachingV2Api } from '../api';
import type { TeachingImageData } from '../api';

interface UseTeachingImageResult {
  imageUrl: string | null;
  imageData: TeachingImageData | null;
  loading: boolean;
  error: string | null;
}

/**
 * 获取教学图片的Hook
 * @param imageId 图片ID
 * @returns 图片URL、数据、加载状态和错误信息
 */
export function useTeachingImage(imageId: string | null): UseTeachingImageResult {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageData, setImageData] = useState<TeachingImageData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!imageId) {
      setImageUrl(null);
      setImageData(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    teachingV2Api.getImage(imageId)
      .then(response => {
        if (response.data.success && response.data.data) {
          setImageData(response.data.data);
          setImageUrl(response.data.data.url);
        } else {
          setError('图片不存在');
        }
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : '获取图片失败');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [imageId]);

  return { imageUrl, imageData, loading, error };
}

/**
 * 图片缓存管理
 */
const imageCache = new Map<string, TeachingImageData>();

/**
 * 清除图片缓存
 */
export function clearImageCache() {
  imageCache.clear();
}

/**
 * 预加载图片
 * @param imageIds 图片ID列表
 */
export async function preloadImages(imageIds: string[]): Promise<void> {
  const promises = imageIds.map(async (id) => {
    if (!imageCache.has(id)) {
      try {
        const response = await teachingV2Api.getImage(id);
        if (response.data.success && response.data.data) {
          imageCache.set(id, response.data.data);
        }
      } catch (error) {
        console.error(`Failed to preload image ${id}:`, error);
      }
    }
  });

  await Promise.allSettled(promises);
}

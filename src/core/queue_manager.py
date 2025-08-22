"""
Queue management system with advanced features
Handles track queuing, shuffling, and loop modes
"""

import asyncio
from typing import Optional, List, Any
import random
from collections import deque
import wavelink


class QueueManager:
    """Advanced queue manager with gaming features"""

    def __init__(self, max_size: int = 1000):
        self._queue = deque()
        self._history = deque(maxlen=50)  # Keep last 50 played tracks
        self._loop_queue = []  # Store original queue for loop mode
        self.max_size = max_size
        self._lock = asyncio.Lock()

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0

    def __len__(self) -> int:
        """Get queue length"""
        return len(self._queue)

    def __iter__(self):
        """Make queue iterable"""
        return iter(self._queue)

    async def put(self, track: wavelink.Playable) -> bool:
        """Add track to queue"""
        async with self._lock:
            if len(self._queue) >= self.max_size:
                return False

            self._queue.append(track)
            return True

    async def put_front(self, track: wavelink.Playable) -> bool:
        """Add track to front of queue (priority)"""
        async with self._lock:
            if len(self._queue) >= self.max_size:
                return False

            self._queue.appendleft(track)
            return True

    async def get(self) -> Optional[wavelink.Playable]:
        """Get next track from queue"""
        async with self._lock:
            if self.is_empty:
                return None

            track = self._queue.popleft()
            self._history.append(track)
            return track

    async def peek(self, index: int = 0) -> Optional[wavelink.Playable]:
        """Peek at track without removing it"""
        async with self._lock:
            if index >= len(self._queue):
                return None

            return self._queue[index]

    async def remove(self, index: int) -> Optional[wavelink.Playable]:
        """Remove track at specific index"""
        async with self._lock:
            if index >= len(self._queue):
                return None

            track = self._queue[index]
            del self._queue[index]
            return track

    async def clear(self) -> int:
        """Clear entire queue"""
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            return count

    async def shuffle(self) -> bool:
        """Shuffle the queue"""
        async with self._lock:
            if len(self._queue) < 2:
                return False

            queue_list = list(self._queue)
            random.shuffle(queue_list)
            self._queue = deque(queue_list)
            return True

    async def reverse(self) -> bool:
        """Reverse the queue order"""
        async with self._lock:
            if len(self._queue) < 2:
                return False

            self._queue.reverse()
            return True

    async def move(self, from_index: int, to_index: int) -> bool:
        """Move track from one position to another"""
        async with self._lock:
            if from_index >= len(self._queue) or to_index >= len(self._queue):
                return False

            track = self._queue[from_index]
            del self._queue[from_index]
            self._queue.insert(to_index, track)
            return True

    async def swap(self, index1: int, index2: int) -> bool:
        """Swap two tracks in queue"""
        async with self._lock:
            if index1 >= len(self._queue) or index2 >= len(self._queue):
                return False

            self._queue[index1], self._queue[index2] = self._queue[index2], self._queue[index1]
            return True

    def reset_loop(self):
        """Reset queue for loop mode"""
        if self._loop_queue:
            self._queue.extend(self._loop_queue)

    def save_for_loop(self):
        """Save current queue for loop mode"""
        self._loop_queue = list(self._queue)

    async def get_upcoming(self, count: int = 5) -> List[wavelink.Playable]:
        """Get upcoming tracks without removing them"""
        async with self._lock:
            return list(self._queue)[:count]

    def get_history(self, count: int = 10) -> List[wavelink.Playable]:
        """Get recently played tracks"""
        return list(self._history)[-count:]

    async def deduplicate(self) -> int:
        """Remove duplicate tracks from queue"""
        async with self._lock:
            seen = set()
            new_queue = deque()
            removed = 0

            for track in self._queue:
                track_id = f"{track.title}:{track.author}"
                if track_id not in seen:
                    seen.add(track_id)
                    new_queue.append(track)
                else:
                    removed += 1

            self._queue = new_queue
            return removed

    async def filter_by_duration(self, max_duration: int) -> int:
        """Remove tracks longer than specified duration"""
        async with self._lock:
            new_queue = deque()
            removed = 0

            for track in self._queue:
                if track.length <= max_duration * 1000:  # Convert to milliseconds
                    new_queue.append(track)
                else:
                    removed += 1

            self._queue = new_queue
            return removed

    def to_list(self) -> List[wavelink.Playable]:
        """Convert queue to list"""
        return list(self._queue)

    def get_total_duration(self) -> int:
        """Get total duration of all tracks in queue (seconds)"""
        return sum(track.length // 1000 for track in self._queue)

    async def find(self, query: str) -> List[tuple[int, wavelink.Playable]]:
        """Find tracks in queue matching query"""
        async with self._lock:
            results = []
            query_lower = query.lower()

            for index, track in enumerate(self._queue):
                if (query_lower in track.title.lower() or
                        (track.author and query_lower in track.author.lower())):
                    results.append((index, track))

            return results

    async def prioritize_user_tracks(self, user_id: int) -> int:
        """Move all tracks from a specific user to front"""
        async with self._lock:
            user_tracks = []
            other_tracks = []

            for track in self._queue:
                if hasattr(track, 'requester') and track.requester.id == user_id:
                    user_tracks.append(track)
                else:
                    other_tracks.append(track)

            self._queue = deque(user_tracks + other_tracks)
            return len(user_tracks)

    def get_stats(self) -> dict:
        """Get queue statistics"""
        total_duration = self.get_total_duration()
        unique_requesters = set()
        platforms = {}

        for track in self._queue:
            if hasattr(track, 'requester'):
                unique_requesters.add(track.requester.id)

            # Count platforms (simplified)
            if 'youtube' in track.uri.lower():
                platforms['YouTube'] = platforms.get('YouTube', 0) + 1
            elif 'spotify' in track.uri.lower():
                platforms['Spotify'] = platforms.get('Spotify', 0) + 1
            elif 'soundcloud' in track.uri.lower():
                platforms['SoundCloud'] = platforms.get('SoundCloud', 0) + 1
            else:
                platforms['Other'] = platforms.get('Other', 0) + 1

        return {
            'total_tracks': len(self._queue),
            'total_duration': total_duration,
            'unique_requesters': len(unique_requesters),
            'platforms': platforms,
            'average_duration': total_duration // len(self._queue) if self._queue else 0
        }

from random import choice
import math

def slide_in_effect(clip, duration, video_width, wobble_amplitude=100,  wobble_frequency=100):
            """
            Animates a clip to slide in from the specified side.
            """
            clip_width = clip.size[0]
            
            center_x = video_width / 2 - clip_width / 2

            wobble_duration=duration / 3
            sliding_duration = (2/3) * duration

            side = choice(["left", "right"])

            def position_func(t):
                if t < sliding_duration:
                    # Phase 1: Slide-in animation
                    if side == 'left':
                        # Animate from off-screen left to center
                        return (int(-clip_width + (center_x + clip_width) * (t / sliding_duration)), 'center')
                    else:  # 'right'
                        # Animate from off-screen right to center
                        return (int(video_width - (video_width - center_x) * (t / sliding_duration)), 'center')
                elif t < sliding_duration + wobble_duration:
                    # Phase 2: Wobble effect
                    # Time elapsed since the wobble started
                    wobble_t = t - sliding_duration
                    
                    # Decay factor ensures the wobble stops at the end of wobble_duration
                    decay_factor = (1 - (wobble_t / wobble_duration))**2
                    
                    wobble_offset = wobble_amplitude * math.sin(wobble_frequency * wobble_t) * decay_factor
                    
                    return (int(center_x + wobble_offset), 'center')
                else:
                    # Phase 3: Settle in the center
                    return ('center', 'center')


            return clip.with_position(position_func)
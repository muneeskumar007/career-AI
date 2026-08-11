import { motion, useReducedMotion } from "framer-motion";

/**
 * The brand's signature element — a calibration/audio-meter motif that ties
 * the auth screens to the product's core idea (an AI that listens to and
 * scores your interview). Purely decorative and aria-hidden.
 */
export default function SignalBars({ bars = 24 }) {
  const shouldReduceMotion = useReducedMotion();
  const heights = Array.from({ length: bars }, (_, i) => 6 + ((i * 37) % 26));

  return (
    <div className="flex h-8 items-end gap-[3px]" aria-hidden="true">
      {heights.map((h, i) => (
        <motion.span
          key={i}
          className="w-[3px] rounded-full bg-signal/70"
          style={{ height: h }}
          animate={shouldReduceMotion ? undefined : { scaleY: [0.4, 1, 0.6, 0.9, 0.4] }}
          transition={{
            duration: 1.6 + (i % 5) * 0.15,
            repeat: Infinity,
            ease: "easeInOut",
            delay: (i % 8) * 0.08,
          }}
        />
      ))}
    </div>
  );
}

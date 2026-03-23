import { useEffect, useRef } from 'react';

export default function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const particles = Array.from({ length: 56 }, () => ({
      x: 0,
      y: 0,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      radius: Math.random() * 1.6 + 0.6,
      alpha: Math.random() * 0.45 + 0.08,
    }));

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      particles.forEach((particle) => {
        particle.x = Math.random() * canvas.width;
        particle.y = Math.random() * canvas.height;
      });
    };

    resize();
    window.addEventListener('resize', resize);

    let animationFrame = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x <= 0 || particle.x >= canvas.width) particle.vx *= -1;
        if (particle.y <= 0 || particle.y >= canvas.height) particle.vy *= -1;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 255, 180, ${particle.alpha})`;
        ctx.fill();
      });

      particles.forEach((a, index) => {
        for (let i = index + 1; i < particles.length; i += 1) {
          const b = particles[i]!;
          const distance = Math.hypot(a.x - b.x, a.y - b.y);
          if (distance < 120) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(0, 255, 180, ${0.09 * (1 - distance / 120)})`;
            ctx.stroke();
          }
        }
      });

      animationFrame = window.requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      window.cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
        opacity: 0.55,
      }}
    />
  );
}

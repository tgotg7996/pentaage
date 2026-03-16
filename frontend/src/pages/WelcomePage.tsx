import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface WelcomePageProps {
  onEnter: () => void;
}

class Particle {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  size: number;
  color: string;
  vx: number;
  vy: number;
  baseX: number;
  baseY: number;
  density: number;
  isExploding: boolean;

  constructor(x: number, y: number, targetX: number, targetY: number, color: string, isMobile: boolean) {
    this.x = x;
    this.y = y;
    this.targetX = targetX;
    this.targetY = targetY;
    this.baseX = targetX;
    this.baseY = targetY;
    // Mobile particles are slightly larger for better viewing
    this.size = (Math.random() * 1.5 + 1) * (isMobile ? 1.5 : 1); 
    this.color = color;
    this.vx = 0;
    this.vy = 0;
    this.density = Math.random() * 30 + 10;
    this.isExploding = false;
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.closePath();
    ctx.fill();
  }

  update(mouse: { x: number; y: number; radius: number }, isExploding: boolean, canvasWidth: number, canvasHeight: number) {
    if (isExploding) {
      if (!this.isExploding) {
        // Trigger explosion vector calculation once
        this.isExploding = true;
        const dx = this.x - canvasWidth / 2;
        const dy = this.y - canvasHeight / 2;
        const dist = Math.sqrt(dx * dx + dy * dy);
        // Normalize and apply explosive force
        const force = (Math.random() * 15 + 10);
        this.vx = (dx / dist) * force;
        this.vy = (dy / dist) * force;
      }
      this.x += this.vx;
      this.y += this.vy;
      return;
    }

    // Interactive organic floating/return
    const dx = mouse.x - this.x;
    const dy = mouse.y - this.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const forceDirectionX = dx / distance;
    const forceDirectionY = dy / distance;
    const maxDistance = mouse.radius;
    const force = (maxDistance - distance) / maxDistance;
    const directionX = forceDirectionX * force * this.density;
    const directionY = forceDirectionY * force * this.density;

    if (distance < mouse.radius) {
      this.x -= directionX;
      this.y -= directionY;
    } else {
      if (this.x !== this.baseX) {
        let dx = this.x - this.baseX;
        this.x -= dx / 15; // Return speed constraint
      }
      if (this.y !== this.baseY) {
        let dy = this.y - this.baseY;
        this.y -= dy / 15;
      }
    }
  }
}

export default function WelcomePage({ onEnter }: WelcomePageProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isExploding, setIsExploding] = useState(false);
  const [particlesLoaded, setParticlesLoaded] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    let particles: Particle[] = [];
    let animationFrameId: number;

    const mouse = { x: -9999, y: -9999, radius: 80 };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    
    // Support touch for mobile
    const handleTouchMove = (e: TouchEvent) => {
      if(e.touches.length > 0) {
        mouse.x = e.touches[0].clientX;
        mouse.y = e.touches[0].clientY;
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("touchmove", handleTouchMove);

    const initParticles = () => {
      const isMobile = window.innerWidth <= 768;
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const image = new Image();
      image.src = "/logo.png"; // Load the actual logo

      image.onload = () => {
        // Draw image to sample pixels
        const scale = isMobile ? 0.35 : 0.5; // Scale logo appropriately
        const scaledWidth = image.width * scale;
        const scaledHeight = image.height * scale;
        const offsetX = (canvas.width - scaledWidth) / 2;
        const offsetY = (canvas.height - scaledHeight) / 2 - 50; // shift up slightly

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, offsetX, offsetY, scaledWidth, scaledHeight);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles = [];
        // Extract pixels
        const gap = isMobile ? 4 : 3; // Particle spacing
        for (let y = 0; y < canvas.height; y += gap) {
          for (let x = 0; x < canvas.width; x += gap) {
            const index = (y * canvas.width + x) * 4;
            const alpha = imageData.data[index + 3];

            // If pixel is not transparent
            if (alpha > 128) {
              const r = imageData.data[index];
              const g = imageData.data[index + 1];
              const b = imageData.data[index + 2];
              const color = `rgba(${r}, ${g}, ${b}, ${alpha / 255})`;

              // Start from random edge of screen
              let startX, startY;
              const edge = Math.floor(Math.random() * 4);
              if (edge === 0) { startX = Math.random() * canvas.width; startY = -50; }
              else if (edge === 1) { startX = canvas.width + 50; startY = Math.random() * canvas.height; }
              else if (edge === 2) { startX = Math.random() * canvas.width; startY = canvas.height + 50; }
              else { startX = -50; startY = Math.random() * canvas.height; }

              particles.push(new Particle(startX, startY, x, y, color, isMobile));
            }
          }
        }
        setParticlesLoaded(true);
      };
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw inner glow if exploding
      if(isExploding) {
          ctx.fillStyle = "rgba(107, 192, 109, 0.05)";
          ctx.fillRect(0,0, canvas.width, canvas.height);
      }

      for (let i = 0; i < particles.length; i++) {
        particles[i].draw(ctx);
        particles[i].update(mouse, isExploding, canvas.width, canvas.height);
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    const handleResize = () => {
      // Re-init particles to fit new aspect ratios, except when exploding
      if (!isExploding) {
        initParticles();
      }
    };
    window.addEventListener("resize", handleResize);

    initParticles();
    animate();

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isExploding]);

  const handleEnterClick = () => {
    setIsExploding(true);
    // Wait for explosion animation to finish before unmounting/routing
    setTimeout(() => {
      onEnter();
    }, 1200); 
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "var(--color-bg)",
        zIndex: 1000,
        overflow: "hidden",
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 1,
          pointerEvents: "none", // let clicks pass through to button
        }}
      />
      
      {/* Title & Button Overlay */}
      <AnimatePresence>
        {!isExploding && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: particlesLoaded ? 1 : 0 }}
            exit={{ opacity: 0, scale: 1.1, filter: "blur(10px)" }}
            transition={{ duration: 0.8 }}
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              pointerEvents: "none", // Allow mouse events to reach canvas underneath if needed
            }}
          >
            <div style={{ marginTop: "180px", textAlign: "center", pointerEvents: "auto" }}>
              <h1 style={{ 
                fontSize: "var(--text-4xl)", 
                fontWeight: 800, 
                color: "var(--color-text)", 
                letterSpacing: "-1.5px", 
                marginBottom: "var(--space-xs)",
              }}>
                PentaAge
              </h1>
              <p style={{ 
                fontSize: "var(--text-lg)", 
                color: "var(--color-text-secondary)", 
                letterSpacing: "6px", 
                textTransform: "uppercase",
                opacity: 0.8
              }}>
                传统智慧 · 现代计算
              </p>

              <button
                onClick={handleEnterClick}
                className="btn btn-primary"
                style={{
                  marginTop: "var(--space-3xl)",
                  padding: "var(--space-md) var(--space-2xl)",
                  fontSize: "var(--text-lg)",
                  borderRadius: "var(--radius-full)",
                  background: "var(--color-text)",
                  color: "var(--color-bg)",
                  fontWeight: 600,
                  border: "none",
                  boxShadow: "0 8px 20px -10px var(--color-text)",
                  cursor: "pointer",
                }}
              >
                进入系统
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

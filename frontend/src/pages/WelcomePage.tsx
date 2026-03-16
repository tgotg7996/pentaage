import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/welcome.css";

interface WelcomePageProps {
  onEnter: () => void;
}

class AmbientParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  color: string;

  constructor(width: number, height: number) {
    this.x = Math.random() * width;
    this.y = Math.random() * height;
    this.vx = (Math.random() - 0.5) * 0.3;
    this.vy = (Math.random() - 0.5) * 0.3;
    this.size = Math.random() * 2 + 1;
    this.alpha = Math.random() * 0.4 + 0.1;
    this.color = `rgba(107, 192, 109, ${this.alpha})`;
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.fillStyle = this.color;
    ctx.shadowBlur = 8;
    ctx.shadowColor = "rgba(107, 192, 109, 0.5)";
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  update(mouse: { x: number; y: number; radius: number }, width: number, height: number, isExploding: boolean) {
    if (isExploding) {
      this.x += this.vx * 5;
      this.y += this.vy * 5;
      this.alpha *= 0.96;
      this.color = `rgba(107, 192, 109, ${this.alpha})`;
      return;
    }

    this.x += this.vx;
    this.y += this.vy;

    if (this.x < 0) this.x = width;
    if (this.x > width) this.x = 0;
    if (this.y < 0) this.y = height;
    if (this.y > height) this.y = 0;

    const dx = mouse.x - this.x;
    const dy = mouse.y - this.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < 150) {
      const force = (150 - distance) / 150;
      this.x -= dx * force * 0.02;
      this.y -= dy * force * 0.02;
    }
  }
}

class Particle {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  size: number;
  baseColor: { r: number; g: number; b: number; a: number };
  color: string;
  vx: number;
  vy: number;
  baseX: number;
  baseY: number;
  density: number;
  isExploding: boolean;
  angle: number;
  velocity: number;
  randomDriftOffset: number;

  constructor(x: number, y: number, targetX: number, targetY: number, r: number, g: number, b: number, a: number, isMobile: boolean) {
    this.x = x;
    this.y = y;
    this.targetX = targetX;
    this.targetY = targetY;
    this.baseX = targetX;
    this.baseY = targetY;
    // Mobile particles are slightly larger for better viewing
    this.size = (Math.random() * 1.5 + 0.8) * (isMobile ? 1.5 : 1); 
    this.baseColor = { r, g, b, a };
    this.color = `rgba(${r}, ${g}, ${b}, ${a})`;
    this.vx = 0;
    this.vy = 0;
    // Density determines how resistant to mouse forces they are
    this.density = Math.random() * 40 + 20;
    this.isExploding = false;
    
    // For organic drift animation
    this.angle = Math.random() * Math.PI * 2;
    this.velocity = Math.random() * 0.015 + 0.005; // Slow flow
    this.randomDriftOffset = Math.random() * 3 + 1; // Range of drifting (1-4px)
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

    // Continuous smooth organic drift
    this.angle += this.velocity;
    const driftX = Math.cos(this.angle) * this.randomDriftOffset;
    const driftY = Math.sin(this.angle) * this.randomDriftOffset;

    // Subtle color gradient fluctuation (modulating lightness slightly)
    const lightnessShift = Math.sin(this.angle) * 20; // max shift of 20
    this.color = `rgba(${Math.min(255, Math.max(0, this.baseColor.r + lightnessShift))}, ${Math.min(255, Math.max(0, this.baseColor.g + lightnessShift))}, ${Math.min(255, Math.max(0, this.baseColor.b + lightnessShift))}, ${this.baseColor.a})`;

    // Interactive mouse repulsion
    const dx = mouse.x - this.x;
    const dy = mouse.y - this.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance < mouse.radius) {
      const forceDirectionX = dx / distance;
      const forceDirectionY = dy / distance;
      // Soften the force curve
      const force = (mouse.radius - distance) / mouse.radius;
      // Reduce the density multiplier for gentler repulsion, so they don't fly off too far
      const directionX = forceDirectionX * force * (this.density * 0.3);
      const directionY = forceDirectionY * force * (this.density * 0.3);
      this.x -= directionX;
      this.y -= directionY;
    } else {
      // Soft return to base target + continuous fluid drift
      const targetFlowX = this.baseX + driftX;
      const targetFlowY = this.baseY + driftY;
      
      this.x += (targetFlowX - this.x) * 0.05; // 0.05 is the return spring factor
      this.y += (targetFlowY - this.y) * 0.05;
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
    let ambientParticles: AmbientParticle[] = [];
    let animationFrameId: number;

    const mouse = { x: -9999, y: -9999, radius: 45 }; // Reduced disturbance radius

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

      // Init ambient particles
      ambientParticles = [];
      const ambientCount = isMobile ? 40 : 100;
      for (let i = 0; i < ambientCount; i++) {
        ambientParticles.push(new AmbientParticle(canvas.width, canvas.height));
      }

      const image = new Image();
      image.src = "/logo.png"; // Load the actual logo

      image.onload = () => {
        // Draw image to sample pixels
        const scale = isMobile ? 0.8 : 1.2; // Slightly reduced scale for better balance
        const scaledWidth = image.width * scale;
        const scaledHeight = image.height * scale;
        const offsetX = (canvas.width - scaledWidth) / 2;
        const offsetY = (canvas.height - scaledHeight) / 2 - (isMobile ? 80 : 160); 

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, offsetX, offsetY, scaledWidth, scaledHeight);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles = [];
        // Extract pixels
        const gap = isMobile ? 3 : 3; // Slightly increased gap so performance doesn't tank with the massive scale
        for (let y = 0; y < canvas.height; y += gap) {
          for (let x = 0; x < canvas.width; x += gap) {
            const index = (y * canvas.width + x) * 4;
            const alpha = imageData.data[index + 3];

            // If pixel is not transparent
            if (alpha > 128) {
              const r = imageData.data[index];
              const g = imageData.data[index + 1];
              const b = imageData.data[index + 2];
              
              // CRITICAL: Filter out the near-white background pixels that form the faint box block in the PNG
              if (r > 240 && g > 240 && b > 240) continue;

              // Start from random edge of screen
              let startX: number, startY: number;
              const edge = Math.floor(Math.random() * 4);
              if (edge === 0) { startX = Math.random() * canvas.width; startY = -50; }
              else if (edge === 1) { startX = canvas.width + 50; startY = Math.random() * canvas.height; }
              else if (edge === 2) { startX = Math.random() * canvas.width; startY = canvas.height + 50; }
              else { startX = -50; startY = Math.random() * canvas.height; }

              particles.push(new Particle(startX, startY, x, y, r, g, b, alpha / 255, isMobile));
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

      // Update and draw ambient particles & connections
      ctx.lineWidth = 0.5;
      for (let i = 0; i < ambientParticles.length; i++) {
        ambientParticles[i].update(mouse, canvas.width, canvas.height, isExploding);
        ambientParticles[i].draw(ctx);

        // Connections (Meridian effect) - only draw if not exploding
        if (!isExploding) {
          for (let j = i + 1; j < ambientParticles.length; j++) {
            const dx = ambientParticles[i].x - ambientParticles[j].x;
            const dy = ambientParticles[i].y - ambientParticles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 120) {
              const opacity = (1 - dist / 120) * 0.2;
              ctx.strokeStyle = `rgba(107, 192, 109, ${opacity})`;
              ctx.beginPath();
              ctx.moveTo(ambientParticles[i].x, ambientParticles[i].y);
              ctx.lineTo(ambientParticles[j].x, ambientParticles[j].y);
              ctx.stroke();
            }
          }
        }
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
            exit={{ opacity: 0, scale: 1.05, filter: "blur(15px)" }}
            transition={{ duration: 1 }}
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              pointerEvents: "none",
            }}
          >
            <motion.div 
              style={{ 
                marginTop: window.innerWidth <= 768 ? "120px" : "240px", 
                textAlign: "center", 
                pointerEvents: "auto" 
              }}
              className="text-glass-backdrop"
              variants={{
                hidden: { opacity: 0, scale: 0.95 },
                visible: {
                  opacity: 1,
                  scale: 1,
                  transition: { staggerChildren: 0.2, delayChildren: 0.4, duration: 1.2, ease: "easeOut" }
                }
              }}
              initial="hidden"
              animate={particlesLoaded ? "visible" : "hidden"}
            >
              <motion.h1 
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 1, ease: [0.25, 0.1, 0.25, 1] } }
                }}
                className="animated-title"
                style={{ 
                  fontSize: window.innerWidth <= 768 ? "3rem" : "5rem", 
                  fontWeight: 900, 
                  letterSpacing: "-2px", 
                  marginBottom: "var(--space-md)",
                  lineHeight: 1.1,
                }}
              >
                PentaAge
              </motion.h1>

              <motion.div 
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 1, ease: [0.25, 0.1, 0.25, 1] } }
                }}
                className="subtitle-container"
              >
                <div className="subtitle-line" />
                <p 
                  style={{ 
                    fontSize: window.innerWidth <= 768 ? "0.875rem" : "1.125rem", 
                    color: "var(--color-text)", 
                    letterSpacing: "0.5em", 
                    fontWeight: 500,
                    opacity: 1,
                    margin: 0,
                    whiteSpace: "nowrap",
                    textTransform: "uppercase"
                  }}
                >
                  传统智慧 · 现代计算
                </p>
                <div className="subtitle-line" />
              </motion.div>

              <motion.button
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 1, ease: [0.25, 0.1, 0.25, 1] } }
                }}
                whileHover={{ 
                  scale: 1.05, 
                  y: -3 
                }}
                whileTap={{ scale: 0.95 }}
                onClick={handleEnterClick}
                className="premium-button pulse-animation"
                style={{
                  marginTop: "var(--space-2xl)",
                  padding: "16px 56px",
                  fontSize: "1.125rem",
                  borderRadius: "99px",
                  color: "white",
                  fontWeight: 600,
                  cursor: "pointer",
                  letterSpacing: "5px",
                  pointerEvents: "auto"
                }}
              >
                进入系统
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

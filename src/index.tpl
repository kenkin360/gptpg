<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Moebius Track - Function.extend.js + Three.js</title>
  <style>
    body { margin: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
  <script src="https://cdn.jsdelivr.net/gh/kenkin360/Function.extend/Function.extend.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@latest/build/three.min.js"></script>

  <script>
    var MainApp = Function.extend(Object, function () {
      var _ = this(MainApp);

      function MainApp() {
        _['base'].apply(this, arguments);
        this.scene = new THREE.Scene();

        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.z = 5;

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(this.renderer.domElement);

        var light = new THREE.DirectionalLight(0xffffff, 1);
        light.position.set(5, 5, 5);
        this.scene.add(light);

        var ambient = new THREE.AmbientLight(0x888888);
        this.scene.add(ambient);

        this.createMoebius();
        this.animate();
      }

      _['private'].mesh = null;

      _['public'].createMoebius = function () {
        function moebius(u, t, target) {
          u *= Math.PI;
          t *= 2 * Math.PI;
          u = u * 2;
          var major = 1.5, a = 0.5;
          var x = Math.cos(t) * (major + a * Math.cos(u) * Math.cos(t / 2));
          var y = Math.sin(t) * (major + a * Math.cos(u) * Math.cos(t / 2));
          var z = a * Math.sin(u) * Math.cos(t / 2);
          target.set(x, y, z);
        }

        var geometry = new THREE.ParametricGeometry(moebius, 100, 20);
        var material = new THREE.MeshStandardMaterial({ color: 0xff0000, wireframe: false, side: THREE.DoubleSide });
        _(this).mesh = new THREE.Mesh(geometry, material);
        this.scene.add(_(this).mesh);
      };

      _['public'].animate = function () {
        requestAnimationFrame(this.animate.bind(this));
        if (_(this).mesh) {
          _(this).mesh.rotation.x += 0.005;
          _(this).mesh.rotation.y += 0.01;
        }
        this.renderer.render(this.scene, this.camera);
      };
    });

    new MainApp();
  </script>
</body>
</html>

# Build optimization (this machine)

Target: 13th Gen Intel Core i5-1335U (Raptor Lake-U, 2P+8E), AVX2+FMA, no AVX-512.

```sh
export CFLAGS="-O3 -march=native -mtune=native -flto -fno-plt -pipe -DNDEBUG"
export CXXFLAGS="$CFLAGS"
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS_RELEASE="$CFLAGS" \
      -DCMAKE_CXX_FLAGS_RELEASE="$CXXFLAGS"
cmake --build build -j12
```

Notes:
- `-march=native` here means `-mavx2 -mfma -mbmi2 -mpopcnt`; never add `-mavx512*`.
- PGO: build with `-fprofile-generate`, run a representative workload, rebuild with
  `-fprofile-use -fprofile-correction`.
- Only use `-ffast-math` if the code does not rely on IEEE edge cases.

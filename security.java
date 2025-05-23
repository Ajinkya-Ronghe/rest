import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.config.http.SessionCreationPolicy;

@EnableWebSecurity
public class SecurityConfig {

    // Inject the custom property from application.properties
    @Value("${security.authentication.enabled}")
    private boolean authenticationEnabled;

    // Define an in-memory user with username, password, and roles
    @Bean
    public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
        UserDetails user = User.builder()
                .username("user")
                .password(passwordEncoder.encode("password"))  // Properly encode the password
                .roles("USER")
                .build();

        return new InMemoryUserDetailsManager(user);
    }

    // Password encoder bean
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();  // Use BCryptPasswordEncoder
    }

    // Configure security for all HTTP requests
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        if (authenticationEnabled) {
            // Authentication is enabled
            http
                .csrf().disable()  // Disable CSRF protection for APIs
                .authorizeRequests()
                    .anyRequest().authenticated()  // Require authentication for all requests
                    .and()
                .httpBasic()  // Use basic authentication
                .and()
                .sessionManagement()
                    .sessionCreationPolicy(SessionCreationPolicy.STATELESS);  // Disable session creation
        } else {
            // Authentication is disabled
            http
                .csrf().disable()  // Disable CSRF protection
                .authorizeRequests()
                    .anyRequest().permitAll();  // Allow all requests without authentication
        }

        return http.build();
    }
}

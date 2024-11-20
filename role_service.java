import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class RoleService {

    private final JdbcTemplate jdbcTemplate;
    private final SecurityQueries securityQueries;

    @Autowired
    public RoleService(JdbcTemplate jdbcTemplate, SecurityQueries securityQueries) {
        this.jdbcTemplate = jdbcTemplate;
        this.securityQueries = securityQueries;
    }

    public String getRequiredAuthority() {
        // Use the query defined in SecurityQueries
        return jdbcTemplate.queryForObject(securityQueries.getRequiredAuthorityQuery(), String.class);
    }
}
